# -*- coding: utf-8 -*-
import locale
import os
import json
import threading
import sys
from typing import Dict, Any
from core.path_core import PathCore

class LocalizationCore:
    def __init__(self):
        self._lock = threading.Lock()
        self.config_path = PathCore.get_config_path("settings.json")
        self.locales_path = PathCore.get_config_path("locales.json")
        
        self.system_lang = "en" # Global fallback
        self._matrices: Dict[str, Dict[str, Any]] = {}
        
        # Hårdkodad nöd-fallback om locales.json är helt korrupt eller saknas
        self._hardcoded_fallback = {
            "en": {
                "voice_modes": ["OFF", "PTT", "LISTEN"],
                "app_title": "Voice Assistant",
                "status_ready": "Ready"
            },
            "sv": {
                "voice_modes": ["AV", "PTT", "LYSSNA"],
                "app_title": "Röstassistent",
                "status_ready": "Redo"
            }
        }
        
        # Läs in den externa JSON-datafilen omedelbart vid boot
        self.load_locales_from_disk()
        self.initialize_localization()

    def load_locales_from_disk(self) -> None:
        """Loads unstructured translation dictionaries transactionally into the memory map."""
        with self._lock:
            if os.path.exists(self.locales_path):
                try:
                    with open(self.locales_path, "r", encoding="utf-8") as f:
                        self._matrices = json.load(f)
                    print(f"[LOCALIZATION] Successfully serialized {len(self._matrices)} language matrices from disk.")
                except Exception as e:
                    print(f"[LOCALIZATION-ERROR] Failed to parse locales.json: {e}. Armed hardcoded fallbacks.")
                    # Sätt nöd-fallbacken om JSON-filen är korrupt
                    self._matrices = self._hardcoded_fallback.copy()
            else:
                print(f"[LOCALIZATION-WARNING] External data layer missing at {self.locales_path}. Fallbacks armed.")
                # Sätt nöd-fallbacken om filen saknas helt
                self._matrices = self._hardcoded_fallback.copy()

    def initialize_localization(self) -> None:
        """Determines the active host language vector transactionally at boot."""
        with self._lock:
            has_forced_preference = False
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    forced_lang = config.get("forced_language", "")
                    if forced_lang in self._matrices:
                        self.system_lang = forced_lang
                        has_forced_preference = True
                except Exception:
                    pass

            if not has_forced_preference:
                detected_iso = ""
                if sys.platform == "win32":
                    try:
                        import ctypes
                        # Förbättrad felhantering för ctypes-anropet
                        LOCALE_SISO639LANGNAME = 0x00000059
                        buf = ctypes.create_unicode_buffer(9)
                        result = ctypes.windll.kernel32.GetLocaleInfoW(0x0400, LOCALE_SISO639LANGNAME, buf, 9)
                        if result > 0:
                            detected_iso = buf.value.lower().strip()
                    except Exception:
                        pass

                if not detected_iso:
                    try:
                        for env_var in ["LANG", "LC_ALL", "LC_CTYPE"]:
                            val = os.environ.get(env_var, "").lower()
                            if "_" in val:
                                detected_iso = val.split("_")[0]
                                break
                            elif val:
                                detected_iso = val
                                break
                    except Exception:
                        pass

                if not detected_iso:
                    try:
                        loc = locale.getdefaultlocale() or locale.getlocale()
                        if loc and loc[0]:
                            detected_iso = loc[0].lower().split("_")[0]
                    except Exception:
                        pass

                if detected_iso in self._matrices:
                    self.system_lang = detected_iso
                else:
                    self.system_lang = "en"
            
            print(f"[LOCALIZATION] System language transaction bound to context: [{self.system_lang.upper()}]")

    def get_text(self, key: str) -> str:
        with self._lock:
            # Hämta från aktivt språk, fall tillbaka på engelska, fall tillbaka på hårdkodad engelska om allt raderats
            matrix = self._matrices.get(
                self.system_lang, 
                self._matrices.get("en", self._hardcoded_fallback.get("en", {}))
            )
            return matrix.get(key, f"[{key.upper()}_MISSING]")

    def get_voice_modes(self) -> list:
        with self._lock:
            matrix = self._matrices.get(
                self.system_lang, 
                self._matrices.get("en", self._hardcoded_fallback.get("en", {}))
            )
            return list(matrix.get("voice_modes", ["OFF", "PTT", "LISTEN"]))
