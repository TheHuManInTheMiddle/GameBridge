# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
 - HÄMTAR FRÅN: ai/ollama_client.py, core/io_layer.py, core/channel_matrix.py, functions/router_functions.py
 - ANROPAS AV: functions/bridge_functions.py

"""

import threading
from functions.router_functions import function_pipeline_worker

class CognitiveRouterCore:
    def __init__(self, ai_client=None, matrix=None, io_layer=None, core_parent=None):
        self.ai_client = ai_client
        self.matrix = matrix
        self.io_layer = io_layer
        self.core_parent = core_parent  # Context binding to extract live capability toggles (e.g. internet_ai_enabled)

    def route_transactional_flow(self, user_text: str, active_adapter, adapter_folder: str, gui_log_callback, ui_status_callback, speech_callback) -> None:
        """Asynchronously dispatches token evaluation to the functional backend to keep UI metrics completely fluid."""
        threading.Thread(
            target=function_pipeline_worker,
            args=(self, user_text, active_adapter, adapter_folder, gui_log_callback, ui_status_callback, speech_callback),
            daemon=True
        ).start()
