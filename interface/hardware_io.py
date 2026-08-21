# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: None (Strictly isolated hardware abstraction boundary).
 - CALLED BY: core/bridge_core.py, core/voice_core.py
"""
import keyboard
import time

class HardwareIO:
    def __init__(self):
        self.is_listening = False
        # Initialize the state flag directly to prevent AttributeError in concurrent threads
        self.key_released_event = False

    def normalize_key(self, raw_key: str) -> str:
        """Normalizes common Windows modifier key aliases for the keyboard hook system."""
        cleaned = str(raw_key).lower().strip()
        if cleaned in ["left ctrl", "right ctrl", "lctrl", "rctrl"]:
            return "ctrl"
        if cleaned in ["left shift", "right shift", "lshift", "rshift"]:
            return "shift"
        if cleaned in ["left alt", "right alt", "alt gr"]:
            return "alt"
        return cleaned

    def block_until_release(self, target_key: str, running_check_callback):
        """Monitors the key state smoothly without hijacking OS sound card buffers."""
        normalized = self.normalize_key(target_key)
        self.key_released_event = False
        
        try:
            # Active wait loop checking if the physical key is still depressed
            while keyboard.is_pressed(normalized) and running_check_callback():
                time.sleep(0.02)
            # Flip the transaction state flag to signal VoiceCore upon release
            self.key_released_event = True
        except Exception as e:
            print(f"[HARDWARE-ERROR] Key state release check faulted: {e}")
            self.key_released_event = True

