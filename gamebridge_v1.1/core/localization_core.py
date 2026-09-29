# -*- coding: utf-8 -*-

import locale
import os
import json
import threading
import sys
from typing import Dict, Any

from core.path_core import PathCore
from core.config_core import ConfigCore


class LocalizationCore:

    def __init__(self):
        self._lock = threading.Lock()

        self.config_manager = ConfigCore()

        self.config_path = (
            self.config_manager.config_path
        )

        self.locales_path = PathCore.get_config_path(
            "locales.json"
        )

        self.system_lang = "en"
        self._matrices: Dict[str, Dict[str, Any]] = {}

        # Emergency fallback if locales.json is missing or corrupted.
        #
        # GUI icons intentionally use descriptive placeholders here.
        # Actual emoji/icon presentation belongs in locales.json.
        self._hardcoded_fallback = {
            "en": {
                "voice_modes": [
                    "OFF",
                    "PTT",
                    "LISTEN"
                ],

                "app_title": "Voice Assistant",
                "status_ready": "Ready",

                # --------------------------------------------------
                # GUI ICONS
                # --------------------------------------------------

                "icon_status_indicator": "STATUS_INDICATOR",

                "icon_voice_mode_off": "VOICE_OFF",
                "icon_voice_mode_ptt": "VOICE_PTT",
                "icon_voice_mode_persistent": "VOICE_LISTEN",

                "icon_tgblock_locked": "TGBLOCK_LOCKED",
                "icon_tgblock_unlocked": "TGBLOCK_UNLOCKED",

                "icon_ptt_hotkey_capture": "PTT_HOTKEY_CAPTURE",
                "icon_ptt_hotkey": "PTT_HOTKEY",

                "icon_text_size": "TEXT_SIZE",
                "icon_text_color": "TEXT_COLOR",
                "icon_monitor": "MONITOR",

                # --------------------------------------------------
                # GUI TEXT
                # --------------------------------------------------

                "status": "Status",

                "ai_toggle": "AI Active",
                "internet_toggle": "Internet AI",
                "memory_toggle": "Memory",

                "boot_btn": "Launch / Attach App",
                "disconnect_btn": "Disconnect",

                "no_adapter": "No Adapter Loaded",

                "matrix_title": "CHANNEL CONTROL",

                "chat_switch": "Text Chat",
                "voice_label": "Voice Mode:",

                "voice_user_label": "User",
                "voice_ai_label": "AI",

                "telemetry_switch": "Read Telemetry",
                "write_switch": "Write to Adapter",

                "input_placeholder": "Type message...",
                "send_btn": "Send",

                "topmost_toggle": "Stay on Top",

                "text_size_label": "Large Text",
                "text_color_label": "Black Text",
                "monitor_label": "K2 Mon",

                "settings_btn": "Settings",
                "reset_btn": "Reset",

                "duplicate_plugin_title": "Duplicate plugin detected"
            },

            "sv": {
                "voice_modes": [
                    "AV",
                    "PTT",
                    "LYSSNA"
                ],

                "app_title": "Röstassistent",
                "status_ready": "Redo",

                # --------------------------------------------------
                # GUI ICONS
                # --------------------------------------------------

                "icon_status_indicator": "STATUS_INDICATOR",

                "icon_voice_mode_off": "VOICE_OFF",
                "icon_voice_mode_ptt": "VOICE_PTT",
                "icon_voice_mode_persistent": "VOICE_LISTEN",

                "icon_tgblock_locked": "TGBLOCK_LOCKED",
                "icon_tgblock_unlocked": "TGBLOCK_UNLOCKED",

                "icon_ptt_hotkey_capture": "PTT_HOTKEY_CAPTURE",
                "icon_ptt_hotkey": "PTT_HOTKEY",

                "icon_text_size": "TEXT_SIZE",
                "icon_text_color": "TEXT_COLOR",
                "icon_monitor": "MONITOR",

                # --------------------------------------------------
                # GUI TEXT
                # --------------------------------------------------

                "status": "Status",

                "ai_toggle": "AI Aktiv",
                "internet_toggle": "Internet AI",
                "memory_toggle": "Minne",

                "boot_btn": "Starta / Anslut app",
                "disconnect_btn": "Koppla från",

                "no_adapter": "Ingen adapter laddad",

                "matrix_title": "KANALKONTROLL",

                "chat_switch": "Textchatt",
                "voice_label": "Röstläge:",

                "voice_user_label": "Användare",
                "voice_ai_label": "AI",

                "telemetry_switch": "Läs telemetri",
                "write_switch": "Skriv till adapter",

                "input_placeholder": "Skriv meddelande...",
                "send_btn": "Skicka",

                "topmost_toggle": "Alltid överst",

                "text_size_label": "Stor text",
                "text_color_label": "Svart text",
                "monitor_label": "K2 Mon",

                "settings_btn": "Inställningar",
                "reset_btn": "Återställ",

                "duplicate_plugin_title": "Dubblettplugin upptäckt"
            }
        }

        # Read the external JSON data layer immediately at boot.
        self.load_locales_from_disk()
        self.initialize_localization()

    def load_locales_from_disk(self) -> None:
        """
        Loads unstructured translation dictionaries transactionally
        into the memory map.
        """

        with self._lock:

            if os.path.exists(self.locales_path):

                try:

                    with open(
                        self.locales_path,
                        "r",
                        encoding="utf-8"
                    ) as f:

                        self._matrices = json.load(f)

                    print(
                        f"[LOCALIZATION] Successfully serialized "
                        f"{len(self._matrices)} language matrices "
                        f"from disk."
                    )

                except Exception as e:

                    print(
                        "[LOCALIZATION-ERROR] "
                        f"Failed to parse locales.json: {e}. "
                        "Armed hardcoded fallbacks."
                    )

                    self._matrices = (
                        self._hardcoded_fallback.copy()
                    )

            else:

                print(
                    "[LOCALIZATION-WARNING] "
                    f"External data layer missing at "
                    f"{self.locales_path}. "
                    "Fallbacks armed."
                )

                self._matrices = (
                    self._hardcoded_fallback.copy()
                )

    def _detect_system_language(self) -> str:
        """Detects a supported host language from the operating system."""

        detected_iso = ""

        if sys.platform == "win32":

            try:

                import ctypes

                LOCALE_SISO639LANGNAME = 0x00000059

                buf = ctypes.create_unicode_buffer(9)

                result = (
                    ctypes.windll.kernel32.GetLocaleInfoW(
                        0x0400,
                        LOCALE_SISO639LANGNAME,
                        buf,
                        9
                    )
                )

                if result > 0:
                    detected_iso = (
                        buf.value.lower().strip()
                    )

            except Exception:

                pass

        if not detected_iso:

            try:

                for env_var in [
                    "LANG",
                    "LC_ALL",
                    "LC_CTYPE"
                ]:

                    val = os.environ.get(
                        env_var,
                        ""
                    ).lower()

                    if "_" in val:

                        detected_iso = (
                            val.split("_")[0]
                        )

                        break

                    elif val:

                        detected_iso = val
                        break

            except Exception:

                pass

        if not detected_iso:

            try:

                loc = (
                    locale.getdefaultlocale()
                    or locale.getlocale()
                )

                if loc and loc[0]:

                    detected_iso = (
                        loc[0]
                        .lower()
                        .split("_")[0]
                    )

            except Exception:

                pass

        if detected_iso in self._matrices:
            return detected_iso

        return "en"

    def initialize_localization(self) -> None:
        """
        Resolves the persistent system language.

        A saved language in settings.json always takes precedence.
        The host operating system is queried only when no valid
        persistent language is configured.
        """

        with self._lock:

            config = (
                self.config_manager.load_global_config()
            )

            configured_lang = str(
                config.get(
                    "system_language",
                    ""
                )
            ).lower().strip()

            if configured_lang in self._matrices:

                self.system_lang = configured_lang

                print(
                    "[LOCALIZATION] "
                    "Persistent language loaded from configuration: "
                    f"[{self.system_lang.upper()}]"
                )

                return

            self.system_lang = (
                self._detect_system_language()
            )

            config["system_language"] = (
                self.system_lang
            )

            self.config_manager.save_global_config(
                config
            )

            print(
                "[LOCALIZATION] "
                "System language detected and persisted: "
                f"[{self.system_lang.upper()}]"
            )

    def get_text(self, key: str) -> str:

        with self._lock:

            # Get from active language.
            # Fall back to English.
            # Fall back to hardcoded English if necessary.
            matrix = self._matrices.get(
                self.system_lang,
                self._matrices.get(
                    "en",
                    self._hardcoded_fallback.get(
                        "en",
                        {}
                    )
                )
            )

            return matrix.get(
                key,
                f"[{key.upper()}_MISSING]"
            )

    def get_voice_modes(self) -> list:

        with self._lock:

            matrix = self._matrices.get(
                self.system_lang,
                self._matrices.get(
                    "en",
                    self._hardcoded_fallback.get(
                        "en",
                        {}
                    )
                )
            )

            return list(
                matrix.get(
                    "voice_modes",
                    [
                        "OFF",
                        "PTT",
                        "LISTEN"
                    ]
                )
            )