# -*- coding: utf-8 -*-
"""
G.A.M.E. B.R.I.D.G.E. - Main Entry Point

KOPPLINGAR:
 - HÄMTAR FRÅN:
     - core.path_core.py
     - functions/bridge_functions.py
     - interface/client_gui.py
     - core/io_layer.py
     - core/session_manager.py
     - core/channel_matrix.py
     - interface/voice_core.py
     - core/localization_core.py
     - core/telemetry_core.py

 - ANROPAS AV:
     - Direkt terminalexekvering
     - Startskript från valfri katalog

ANSVAR:
 - Förankra projektroten.
 - Ladda lokal miljökonfiguration före övrig applikationsstart.
 - Initiera GameBridges centrala subsystems.
 - Starta GUI och applikationslivscykel.

SÄKERHET:
 - API-nycklar lagras inte i källkoden.
 - .env är lokal konfiguration och ska inte committas.
"""

import os
import sys


# ============================================================================
# 1. PROJEKTROT
# ============================================================================

_CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

_PROJECT_ROOT = os.path.dirname(
    _CURRENT_DIR
)

# Säkerställ att projektets rot alltid finns i Python-sökvägen.
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# ============================================================================
# 2. LOKAL MILJÖKONFIGURATION
# ============================================================================

def _load_local_env():
    """
    Läser projektets lokala .env-fil utan externa Python-beroenden.

    Endast enkla KEY=VALUE-rader används.

    Exempel:

        TAVILY_API_KEY=tvly-xxxxxxxx

    Kommentarer som börjar med '#' ignoreras.

    Befintliga systemmiljövariabler skrivs INTE över.
    Detta gör att en riktig systemvariabel alltid har företräde
    framför .env.

    .env ska aldrig committas till Git.
    """

    env_path = os.path.join(
        _PROJECT_ROOT,
        ".env"
    )

    if not os.path.isfile(env_path):
        print(
            "[SYSTEM] Ingen lokal .env hittades. "
            "Miljövariabler används som de är."
        )
        return

    loaded = 0

    try:
        with open(
            env_path,
            "r",
            encoding="utf-8"
        ) as env_file:

            for raw_line in env_file:
                line = raw_line.strip()

                # Tom rad.
                if not line:
                    continue

                # Kommentar.
                if line.startswith("#"):
                    continue

                # Acceptera även "export KEY=value".
                if line.startswith("export "):
                    line = line[7:].strip()

                if "=" not in line:
                    continue

                key, value = line.split(
                    "=",
                    1
                )

                key = key.strip()
                value = value.strip()

                if not key:
                    continue

                # Ta bort enkla eller dubbla citattecken runt värdet.
                if (
                    len(value) >= 2
                    and value[0] == value[-1]
                    and value[0] in ("'", '"')
                ):
                    value = value[1:-1]

                # Systemmiljövariabler har företräde.
                if key not in os.environ:
                    os.environ[key] = value
                    loaded += 1

        print(
            f"[SYSTEM] Lokal .env laddad: "
            f"{loaded} variabel/variabler."
        )

    except Exception as exc:
        # Ett problem med .env får inte förhindra att
        # GameBridge startar i övrigt.
        print(
            f"[SYSTEM-WARNING] Kunde inte läsa .env: {exc}"
        )


# Ladda .env NU, innan framework-modulerna importeras.
_load_local_env()


# ============================================================================
# 3. GAMEBRIDGE CORE IMPORTS
# ============================================================================

from core.path_core import PathCore

from functions.bridge_functions import GameBridgeCore

from interface.client_gui import GameBridgeGUI

from core.io_layer import GameBridgeIOLayer
from core.session_manager import SessionManager
from core.channel_matrix import ChannelMatrix
from interface.voice_core import VoiceCore
from core.localization_core import LocalizationCore
from core.telemetry_core import TelemetryCore


# ============================================================================
# 4. APPLICATION START
# ============================================================================

def main():
    # Production platform baseline v3.5.0
    print(
        "=== G.A.M.E. B.R.I.D.G.E. "
        "v3.5.0 PLATFORM PRODUCTION BASE ==="
    )

    print(
        "[SYSTEM] Application successfully anchored "
        f"to global root: {PathCore.PROJECT_ROOT}"
    )

    # ------------------------------------------------------------------------
    # Centraliserad core-infrastruktur
    # ------------------------------------------------------------------------

    localizer = LocalizationCore()

    io_layer = GameBridgeIOLayer()

    session_manager = SessionManager()

    matrix = ChannelMatrix()

    # ------------------------------------------------------------------------
    # Asynkron telemetry
    # ------------------------------------------------------------------------

    telemetry_worker = TelemetryCore(
        io_layer=io_layer
    )

    # ------------------------------------------------------------------------
    # Core hub
    # ------------------------------------------------------------------------

    core = GameBridgeCore()

    core.matrix = matrix
    core.io_layer = io_layer
    core.localizer = localizer
    core.telemetry_worker = telemetry_worker

    # ------------------------------------------------------------------------
    # Voice subsystem
    # ------------------------------------------------------------------------

    voice = VoiceCore(
        audio_subsystem=core.audio,
        hardware_subsystem=core.hardware
    )

    core.voice = voice

    # ------------------------------------------------------------------------
    # GUI
    # ------------------------------------------------------------------------

    gui = GameBridgeGUI(
        core_hub=core,
        matrix=matrix,
        localizer=localizer
    )

    # ------------------------------------------------------------------------
    # Cross-link asynchronous communication channels
    # ------------------------------------------------------------------------

    io_layer.register_ui_channel(
        gui.append_log
    )

    core.link_gui(gui)

    # Fire off hardware keyboard vectors and voice confirmation
    # strictly ONCE here.
    core.boot_platform_loops()

    print(
        "[SYSTEM] All decoupled sub-cores successfully mapped "
        "and injected. Launching GUI..."
    )

    # ------------------------------------------------------------------------
    # GUI lifecycle
    # ------------------------------------------------------------------------

    try:
        gui.mainloop()

    except KeyboardInterrupt:
        print(
            "[SYSTEM] Execution interrupted by user. "
            "Flushing memory buffers clean."
        )

    except Exception as exc:
        print(
            "[SYSTEM-NOTIFY] "
            f"Application lifecycle safely terminated: {exc}"
        )


# ============================================================================
# 5. DIRECT EXECUTION
# ============================================================================

if __name__ == "__main__":
    main()