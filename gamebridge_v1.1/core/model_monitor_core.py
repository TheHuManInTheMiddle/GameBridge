# -*- coding: utf-8 -*-

"""
CONNECTIONS:
- FETCHES FROM: selected AI provider
- CALLED BY: main/main.py, interface/client_gui.py
"""

import importlib
import threading
import time


class ModelMonitorCore:
    def __init__(self):
        self._lock = threading.Lock()

    def _get_provider(self, provider_name):
        """Load the selected AI provider module."""

        if not provider_name:
            return None

        try:
            return importlib.import_module(
                f"providers.{provider_name}_ai"
            )

        except Exception:
            return None

    def fetch_installed_models(self, provider_name) -> list:
        """Returns models from the selected AI provider."""

        provider = self._get_provider(provider_name)

        if not provider:
            return ["None"]

        try:
            return provider.get_installed_models()

        except Exception:
            # Even if the selected provider is unavailable,
            # the GUI must still provide a valid neutral model state.
            return ["None"]

    def start_lamp_monitor(
        self,
        core_hub_callback,
        update_lamp_ui_callback,
        get_switch_state_callback,
    ) -> None:
        """Monitors the currently selected AI model."""

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

                    provider_name = core.global_config.get(
                        "ai_provider"
                    )

                    provider = self._get_provider(
                        provider_name
                    )

                    if not provider:
                        update_lamp_ui_callback("#EF4444")
                        time.sleep(3)
                        continue

                    status = provider.get_model_status(
                        core.ai_client
                    )

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