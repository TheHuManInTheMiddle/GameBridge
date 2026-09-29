# -*- coding: utf-8 -*-
"""
plugins/aide_plugin/main_adapter.py

KOPPLINGAR:
  - HÄMTAR FRÅN: adapters/base_adapter.py, core/path_core.py,
    core/adapter_state_core.py
  - ANROPAS AV: adapters/adapter_loader.py (dynamisk plugin-skanner)

ANSVAR:
  - Koppla GameBridge mot AIDE utan att AIDE behöver köra en egen
    nätverks-API — allt sker via headless CLI-anrop (samma princip
    som AIDE:s `--create-report`-kontrakt beskriver) och läsning av
    AIDE:s egna filer på disk (AIDE Box/scan/<projekt>_manifest.json).

ARKITEKTUR (bestämd tillsammans, se AIDE-projektets minnesanteckningar):

    Läsning (telemetri):
        AI begär telemetri
          -> read_telemetry()
          -> senaste manifestet i AIDE Box/scan/
          -> filinnehåll läses direkt från disk
             (manifestet i AIDE Box/scan/ innehåller ABSOLUTA
             källsökvägar, till skillnad från de manifest som
             exporteras/delas externt — se AIDE:s
             core/manifest.py, include_absolute_paths=True)
          -> AI:n resonerar/jämför

    Skrivning (Channel 2):
        AI beslutar rapport
          -> execute_interaction({"action": "create_report", ...})
          -> AIDE startas headless: `<target> --create-report ...`
          -> AIDE Box/report/report.md

    Människan sköter fortfarande all filscanning/-markering i AIDE:s
    egen GUI som vanligt — adaptern varken scannar eller väljer filer
    åt användaren, bara läser resultatet och triggar rapportskrivning.

KANALLÅS (1+1-regeln): plugin_allow_ch2/plugin_allow_telemetry är
pluginets egen sida av dörren. Backend kollar anslutningssidan.
Båda måste vara sanna innan en kanal faktiskt öppnas.
  - plugin_allow_ch2 = True    (create_report kräver skrivkanalen)
  - plugin_allow_telemetry = True  (enda vägen AI:n kan läsa filer
    AIDE triagerar — utan den finns ingen läsväg alls)

KÄND BEGRÄNSNING: om ett AIDE-projekt skannats från FLERA källmappar
samtidigt kan telemetriläsningen inte alltid avgöra säkert vilken
källrot en given relativ sökväg hör till (manifestet lagrar dem inte
parat per fil). Löses genom att pröva varje källrot i tur och ordning
tills en faktisk fil hittas — fungerar för det vanliga enkelrot-fallet
utan undantag.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from typing import Any

from adapters.base_adapter import BaseAdapter
from adapters.adapter_state_core import AdapterStateCore

# Samma gräns som AIDE:s egen core/package_builder.py använder för att
# skydda mot att av misstag dumpa jättefiler som text i telemetrin.
MAX_INLINE_BYTES = 2_000_000

# Vilka Channel 2-actions den här adaptern faktiskt förstår. Allt
# annat loggas och ignoreras defensivt (avsnitt 27-principen — ett
# oväntat payload får aldrig krascha adaptern).
SUPPORTED_ACTIONS = {"create_report"}


class AideAdapter(BaseAdapter):

    def __init__(self):
        super().__init__()

        self.adapter_name = "AIDE (File Triage)"

        # 1+1-kanallåset — pluginets egen sida. Se moduldocstring.
        self.plugin_allow_ch2 = True
        self.plugin_allow_telemetry = True

        self.adapter_folder_name = os.path.basename(
            os.path.dirname(os.path.abspath(__file__))
        )
        self.adapter_state = AdapterStateCore()

        self.target_path = ""
        self.aide_box_path = ""

    # ------------------------------------------------------------------
    # Livscykel
    # ------------------------------------------------------------------

    def initialize(self):
        """Läser sparad konfiguration. Fråga inte om target_path här —
        det hanteras av boot_or_attach() (samma ansvarsfördelning som
        Notepad++-adaptern: initialize() laddar, boot_or_attach() löser
        interaktivt vid behov)."""

        print(f"[{self.adapter_name}] Initialiserar...")

        config = self.adapter_state.load_plugin_config(self.adapter_folder_name)
        saved_target = str(config.get("target_path", "")).strip()

        if saved_target and os.path.isfile(saved_target):
            self.target_path = saved_target
            self.aide_box_path = os.path.join(
                os.path.dirname(saved_target), "AIDE Box"
            )

    def boot_or_attach(self):
        """
        Löser target_path (filväljare vid första körning, annars
        sparat värde), härleder AIDE Box-sökvägen som en fast
        syskonmapp till target_path, och startar AIDE om det inte
        redan kör.

        AIDE behöver INTE hållas vid liv för att adaptern ska fungera
        — telemetriläsning är ren filsystemsläsning och create_report
        körs headless per anrop. Men vi startar/ansluter ändå GUI:t
        här, i linje med GameBridges grundprincip: "starta/anslut ->
        låt applikationen fortsätta köra" — så användaren kan skanna
        och markera filer som vanligt i AIDE:s eget fönster.
        """

        print(f"[{self.adapter_name}] Löser target-sökväg...")

        self.target_path = self.adapter_state.resolve_target_path(
            self.adapter_folder_name
        )

        if not self.target_path:
            print(f"[{self.adapter_name}] Ingen target-applikation vald — avbryter.")
            return

        self.aide_box_path = os.path.join(
            os.path.dirname(self.target_path), "AIDE Box"
        )

        if self._is_already_running():
            print(f"[{self.adapter_name}] AIDE kör redan — ansluten.")
            return

        try:
            subprocess.Popen(self._build_command())
            time.sleep(1.0)
            print(f"[{self.adapter_name}] AIDE startad: {self.target_path}")
        except Exception as e:
            print(f"[{self.adapter_name}] Kunde inte starta AIDE: {e}")

    def shutdown(self):
        """AIDE fortsätter köra oberoende — adaptern kopplar bara ner sin egen sida."""
        print(f"[{self.adapter_name}] Frånkopplad. AIDE fortsätter köra oberoende.")

    # ------------------------------------------------------------------
    # Kapabiliteter
    # ------------------------------------------------------------------

    def get_capabilities(self) -> dict:
        return {
            "interaction_type": "headless_cli",
            "io_tool": "subprocess + AIDE Box-manifest på disk",
            "requires_window_focus": False,
            "requires_external_ai": False,
            "supported_actions": sorted(SUPPORTED_ACTIONS),
            "limitations": (
                "Telemetri speglar bara det senast skannade AIDE-projektet. "
                "Vid flera källmappar i samma skanning löses filsökvägar "
                "bäst-möjligt (varje källrot prövas i tur och ordning)."
            ),
        }

    # ------------------------------------------------------------------
    # Telemetri (läsning: AIDE -> AI)
    # ------------------------------------------------------------------

    def read_telemetry(self) -> dict:
        """
        Läser det senaste manifestet i AIDE Box/scan/ och de markerade
        filernas faktiska innehåll från disk. Ren filsystemsläsning —
        kräver inte att AIDE:s process svarar på något, bara att den
        skannat något minst en gång.
        """
        if not self.target_path or not self.aide_box_path:
            return {"status": "not_configured"}

        manifest_path = self._find_latest_manifest()
        if manifest_path is None:
            return {"status": "no_scan_yet", "aide_box_path": self.aide_box_path}

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            return {"status": "manifest_read_error", "error": str(exc)}

        absolute_roots = manifest.get("source_folders_absolute", [])
        files_payload: dict[str, str] = {}

        for entry in manifest.get("included_files", []):
            rel_path = entry.get("path", "")

            if entry.get("binary"):
                files_payload[rel_path] = "[BINÄR — innehåll ej inkluderat]"
                continue

            abs_path = self._resolve_absolute_path(rel_path, absolute_roots)
            if abs_path is None or not os.path.isfile(abs_path):
                files_payload[rel_path] = "[FIL HITTADES INTE PÅ DISK]"
                continue

            size = entry.get("size_bytes", 0)
            if size > MAX_INLINE_BYTES:
                files_payload[rel_path] = f"[FÖR STOR ({size} bytes) — innehåll ej inkluderat]"
                continue

            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
                    files_payload[rel_path] = fh.read()
            except OSError as exc:
                files_payload[rel_path] = f"[KUNDE INTE LÄSAS: {exc}]"

        return {
            "status": "ok",
            "project": manifest.get("project"),
            "manifest": manifest,
            "files": files_payload,
            "timestamp": time.time(),
        }

    def _find_latest_manifest(self) -> str | None:
        scan_dir = os.path.join(self.aide_box_path, "scan")
        if not os.path.isdir(scan_dir):
            return None

        candidates = [
            os.path.join(scan_dir, name)
            for name in os.listdir(scan_dir)
            if name.lower().endswith("_manifest.json")
        ]
        if not candidates:
            return None

        return max(candidates, key=os.path.getmtime)

    def _resolve_absolute_path(self, rel_path: str, absolute_roots: list[str]) -> str | None:
        """Se KÄND BEGRÄNSNING i moduldocstring."""
        normalized_rel = rel_path.replace("/", os.sep)
        for root in absolute_roots:
            candidate = os.path.join(root, normalized_rel)
            if os.path.isfile(candidate):
                return candidate
        if absolute_roots:
            return os.path.join(absolute_roots[0], normalized_rel)
        return None

    # ------------------------------------------------------------------
    # Channel 2 (skrivning: AI -> AIDE)
    # ------------------------------------------------------------------

    def execute_interaction(self, action_data: Any):
        """
        Accepterar en JSON-sträng eller dict:

            {
                "action": "create_report",
                "report_markdown": "...",
                "project_name": "MittProjekt"   # valfritt
            }

        Kör AIDE headless (`--create-report`) via subprocess — ingen
        levande API-koppling, bara ett engångsanrop som skriver filen
        och avslutar. Se AIDE:s main.py för motparten.
        """
        if not action_data:
            return
        if isinstance(action_data, str) and "[AI-API-ERROR]" in action_data:
            return

        intent_map: dict = {}

        if isinstance(action_data, str):
            cleaned = action_data.strip()
            if cleaned.startswith("{") and cleaned.endswith("}"):
                try:
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, dict):
                        intent_map = parsed
                except (json.JSONDecodeError, TypeError):
                    print(f"[{self.adapter_name}] Kunde inte tolka JSON-payload.")
                    return
        elif isinstance(action_data, dict):
            intent_map = action_data

        action = intent_map.get("action", "")
        if action not in SUPPORTED_ACTIONS:
            print(f"[{self.adapter_name}] Okänd/ostödd action: {action!r} — ignoreras.")
            return

        report_markdown = intent_map.get("report_markdown", "")
        if not isinstance(report_markdown, str) or not report_markdown.strip():
            print(f"[{self.adapter_name}] create_report anropad utan rapportinnehåll.")
            return

        if not self.target_path:
            print(f"[{self.adapter_name}] Ingen target-applikation konfigurerad.")
            return

        project_name = str(intent_map.get("project_name") or "").strip()
        export_dir = os.path.join(self.aide_box_path, "report")

        self._run_create_report(report_markdown, export_dir, project_name)

    def _run_create_report(
        self,
        report_markdown: str,
        export_dir: str,
        project_name: str
    ) -> None:
        tmp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".md",
                delete=False,
                encoding="utf-8"
            ) as tmp:
                tmp.write(report_markdown)
                tmp_path = tmp.name

            command = self._build_command([
                "--create-report",
                "--input",
                tmp_path,
                "--export-dir",
                export_dir,
            ])

            if project_name:
                command += ["--project-name", project_name]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                written_path = result.stdout.strip()
                print(f"[{self.adapter_name}] Rapport skapad: {written_path}")
            else:
                print(
                    f"[{self.adapter_name}] create_report misslyckades: "
                    f"{result.stderr.strip()}"
                )

        except subprocess.TimeoutExpired:
            print(
                f"[{self.adapter_name}] create_report tog för lång tid "
                f"och avbröts."
            )

        except Exception as exc:
            print(
                f"[{self.adapter_name}] Channel 2-körning misslyckades: {exc}"
            )

        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    # ------------------------------------------------------------------
    # Internt
    # ------------------------------------------------------------------

    def _build_command(self, extra_args: list[str] | None = None) -> list[str]:
        """.py-mål körs via samma Python-tolk som GameBridge själv;
        .exe-mål körs direkt."""
        extra_args = extra_args or []

        if self.target_path.lower().endswith(".py"):
            return [sys.executable, self.target_path] + extra_args

        return [self.target_path] + extra_args

    def _is_already_running(self) -> bool:
        """
        Kontrollerar om AIDE redan kör.

        .exe-mål:
            Kontrolleras via tasklist och processnamn.

        .py-mål:
            Kontrolleras via AIDE:s fönstertitel.

        Övriga mål:
            Ingen särskild kontroll utförs och False returneras.
        """

        target_lower = self.target_path.lower()

        # --------------------------------------------------------------
        # .exe -> befintlig processkontroll
        # --------------------------------------------------------------
        if target_lower.endswith(".exe"):
            exe_name = os.path.basename(self.target_path).lower()

            try:
                output = subprocess.check_output(
                    "tasklist",
                    shell=True
                ).decode(
                    "utf-8",
                    errors="ignore"
                )

                return exe_name in output.lower()

            except Exception:
                return False

        # --------------------------------------------------------------
        # .py -> AIDE:s fönstertitel
        # --------------------------------------------------------------
        if target_lower.endswith(".py"):
            try:
                import ctypes

                user32 = ctypes.windll.user32

                target_title = (
                    "A.I.D.E. — Archive · Identify · Determine · Export"
                )

                hwnd = user32.FindWindowW(
                    None,
                    target_title
                )

                return bool(hwnd)

            except Exception:
                return False

        # --------------------------------------------------------------
        # Övriga target-typer -> ingen särskild kontroll
        # --------------------------------------------------------------
        return False