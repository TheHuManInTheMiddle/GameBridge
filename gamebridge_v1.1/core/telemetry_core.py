# -*- coding: utf-8 -*-
"""
CONNECTIONS:
- FETCHES FROM: core/io_layer.py, core/session_manager.py
- CALLED BY: main/main.py, interface/client_gui.py
"""

import threading
import time

class TelemetryCore:
    def __init__(self, io_layer=None):
        self.io_layer = io_layer
        self.loop_active = False
        self.running = True  # MINIMAL FIX: Livscykelflagga för kontrollerad avslutning
        self._lock = threading.Lock()

    def set_loop_state(self, active: bool) -> None:
        """Safely mutates the background loop execution state vector across worker threads."""
        with self._lock:
            self.loop_active = active
            print(f"[TELEMETRY-CORE] Polling background thread status altered to: {active}")

    def start_polling_worker(self, current_adapter_callback, success_ui_callback) -> None:
        """Spawns an isolated thread sequence monitoring active context mutations asynchronously."""
        def worker():
            while self.running:  # MINIMAL FIX: Tråden körs nu bara så länge flaggan är True
                with self._lock:
                    if not self.loop_active:
                        time.sleep(0.5)
                        continue

                active_instance = current_adapter_callback()
                if active_instance and self.io_layer:
                    try:
                        # Transactionally extract backend data streams via core IO layer boundaries
                        telemetry_data = self.io_layer.read_from_kanal_2()
                        if telemetry_data:
                            # Safely pass data back to presentation layer using the UI Queue
                            success_ui_callback(telemetry_data)
                    except Exception as e:
                        print(f"[TELEMETRY-CORE-ERROR] Synchronous backend telemetry extract faulted: {e}")

                time.sleep(1.0) # Standard stable polling interval

        threading.Thread(target=worker, daemon=True).start()
