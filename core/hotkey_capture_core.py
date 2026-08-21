# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: interface/hardware_io.py
 - CALLED BY: core/bridge_core.py
"""

import threading
import keyboard

class HotkeyCaptureCore:
    def __init__(self, hardware_subsystem):
        self.hardware = hardware_subsystem
        self._lock = threading.Lock()

    def capture_next_keypress(self, before_callback, success_callback, final_callback) -> None:
        """Asynchronously intercepts the next keyboard raw event to rebind peripheral triggers."""
        def worker():
            try:
                before_callback()
                recorded_key = keyboard.read_key(suppress=True)
                cleaned_key = self.hardware.normalize_key(recorded_key) if self.hardware else recorded_key
                success_callback(cleaned_key)
            except Exception as e:
                print(f"[HOTKEY-CAPTURE-ERROR] Dynamic key recording faulted: {e}")
            finally:
                final_callback()

        threading.Thread(target=worker, daemon=True).start()

