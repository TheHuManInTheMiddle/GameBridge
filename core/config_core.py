# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: core/path_core.py
 - CALLED BY: core/bridge_core.py, core/cognitive_router_core.py
"""

import json
import os
import threading
from core.path_core import PathCore

class ConfigCore:
    def __init__(self):
        self._lock = threading.Lock()
        self.config_path = PathCore.get_config_path("settings.json")

    def load_global_config(self) -> dict:
        """Resolves system master configuration directories and schemas transactionally."""
        default_config = {"ai_model_name": "sailwind-pilot", "voice_hotkey": "f12"}
        config_dir = os.path.dirname(self.config_path)
        
        with self._lock:
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                        if "voice_hotkey" not in config_data:
                            config_data["voice_hotkey"] = "f12"
                        return config_data
                except Exception:
                    pass
            
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=4)
            except Exception:
                pass
            return default_config

    def save_global_config(self, config_data: dict) -> None:
        """Persists engine configurations safely back to the global disk matrix."""
        with self._lock:
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=4)
            except Exception as e:
                print(f"[CONFIG-ERROR] Failed to save global configuration: {e}")

    def save_adapter_hotkey(self, adapter_folder: str, hotkey: str) -> None:
        """Safely injects and persists a local hotkey bind into a specific plugin manifest."""
        if not adapter_folder or adapter_folder == "None":
            return
            
        config_file = PathCore.get_adapter_file(adapter_folder, "plugin_config.json")
        plugin_data = {}
        
        with self._lock:
            if os.path.exists(config_file):
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        plugin_data = json.load(f)
                except Exception:
                    pass
                    
            plugin_data["voice_hotkey"] = hotkey
            try:
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(plugin_data, f, indent=4)
            except Exception as e:
                print(f"[CONFIG-ERROR] Failed to save adapter configuration: {e}")

