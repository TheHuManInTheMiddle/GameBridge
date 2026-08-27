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
        """Returns the locally installed Ollama models with None as the neutral selection."""
        try:
            model_list_data = ollama.list()

            models = [
                model["model"]
                for model in model_list_data.get("models", [])
                if model.get("model")
            ]

            return ["None"] + models

        except Exception:
            # Even if Ollama is unavailable, the GUI must still
            # provide a valid neutral model state.
            return ["None"]

    def start_lamp_monitor(
        self,
        core_hub_callback,
        update_lamp_ui_callback,
        get_switch_state_callback,
    ) -> None:
        """Monitors the currently selected Ollama model."""

        def worker():
            while True:
                current_core = core_hub_callback()

                if (
                    current_core
                    and hasattr(current_core, "running")
                    and not current_core.running
                ):
                    break

                try:
                    if get_switch_state_callback() == 0:
                        update_lamp_ui_callback("#9CA3AF")
                        time.sleep(1)
                        continue

                    core = core_hub_callback()

                    if not core or not hasattr(core, "ai_client"):
                        update_lamp_ui_callback("#9CA3AF")
                        time.sleep(3)
                        continue

                    selected_model = getattr(
                        core.ai_client,
                        "model_name",
                        "None",
                    )

                    # Neutral state:
                    # No model selected means there is nothing to monitor.
                    if (
                        not selected_model
                        or str(selected_model).strip().lower() == "none"
                    ):
                        update_lamp_ui_callback("#9CA3AF")
                        time.sleep(3)
                        continue

                    status = core.ai_client.check_model_status()

                    if status == "READY":
                        update_lamp_ui_callback("#10B981")

                    elif status == "LOADING":
                        update_lamp_ui_callback("#F59E0B")

                    else:
                        update_lamp_ui_callback("#EF4444")

                except Exception:
                    break

                time.sleep(3)

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()