# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: ai/ollama_client.py
 - CALLED BY: main/main.py, interface/client_gui.py
"""

import threading
import time
import ollama

class ModelMonitorCore:
    def __init__(self):
        self._lock = threading.Lock()

    def fetch_installed_models(self) -> list:
        """Queries local runtime environments to catalog current model inventory states."""
        try:
            model_list_data = ollama.list()
            return [m['model'] for m in model_list_data.get('models', [])]
        except Exception:
            return ["sailwind-pilot"]

    def start_lamp_monitor(self, core_hub_callback, update_lamp_ui_callback, get_switch_state_callback) -> None:
        """Spawns a specialized thread loop monitoring Ollama model availability matrix indexes."""
        def worker():
            while True:
                try:
                    if get_switch_state_callback() == 0:
                        update_lamp_ui_callback("#9CA3AF") # Standard Gray (OFF State)
                        time.sleep(1)
                        continue
                        
                    core = core_hub_callback()
                    if core and hasattr(core, 'ai_client'):
                        status = core.ai_client.check_model_status()
                        if status == "READY":
                            update_lamp_ui_callback("#10B981") # Green
                        elif status == "LOADING":
                            update_lamp_ui_callback("#F59E0B") # Yellow
                        else:
                            update_lamp_ui_callback("#EF4444") # Red
                except Exception:
                    break # Safe thread exit if interface structures tear down at closure
                time.sleep(3)

        threading.Thread(target=worker, daemon=True).start()

