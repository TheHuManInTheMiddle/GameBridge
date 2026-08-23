# -*- coding: utf-8 -*-
"""
CONNECTIONS:
  - FETCHES FROM: Isolated data layer (No external system dependencies).
  - CALLED BY: src/main.py, core/channel_matrix.py (State distribution vector)
"""

import threading
import copy
from typing import Dict, Any

class SessionManager:
    def __init__(self):
        # Thread-safe lock for asynchronous multi-threaded memory access
        self._lock = threading.Lock()
        
        # Standardized runtime state format matching framework specification
        self._state: Dict[str, Any] = {
            "session_active": False,
            "timestamp": 0.0,
            "current_adapter": "None",
            "active_hotkey": "None",          # ADDED: Tracks the active adapter's mapped hotkey dynamically
            "ai_infrastructure_active": False,
            "telemetry": {},
            "interaction_history": []
        }

    def update_state(self, key: str, value: Any) -> None:
        """Updates a specific value within the system runtime state in a thread-safe manner."""
        with self._lock:
            # FIX: Allow dynamic registration of adapter parameters without schema violation crashes
            if key in self._state or key.startswith("adapter_"):
                self._state[key] = value
                print(f"[STATE-UPDATED] Key '{key}' committed safely to runtime context.")
            else:
                # Fallback to absolute structural injection if initialized dynamically by adapter attachment
                self._state[key] = value
                print(f"[STATE-REGISTRATION] Dynamic runtime key '{key}' allocated safely: {value}")

    def set_telemetry(self, telemetry_data: Dict[str, Any]) -> None:
        """Deep-copies and flushes raw telemetry dictionaries into standardized storage."""
        with self._lock:
            self._state["telemetry"] = copy.deepcopy(telemetry_data)

    def get_standardized_state(self) -> Dict[str, Any]:
        """Returns a thread-isolated deep copy of the active state vector for safe reading."""
        with self._lock:
            return copy.deepcopy(self._state)

    def clear_session(self) -> None:
        """Flushes the active session data safely without executing destructive filesystem tasks."""
        with self._lock:
            self._state["telemetry"] = {}
            self._state["interaction_history"] = []
            self._state["current_adapter"] = "None"
            self._state["active_hotkey"] = "None"
            self._state["session_active"] = False
            print("[STATE] Active session parameters safely purged from runtime memory.")

