# -*- coding: utf-8 -*-
"""
CONNECTIONS:
  - FETCHES FROM: Isolated core routing (No external application dependencies).
  - CALLED BY: main/main.py, core/channel_matrix.py
"""

import threading
from typing import Any, Callable, Optional

class GameBridgeIOLayer:
    def __init__(self):
        # Thread synchronization vectors for async stream safety
        self._routing_lock = threading.Lock()
        
        # Channel 1: Conversation links (Registered by GUI or Core)
        self._ui_log_callback: Optional[Callable[[str, str], None]] = None
        
        # Channel 2: Interaction links (Registered dynamically by active adapters)
        self._target_input_callback: Optional[Callable[[Any], None]] = None
        self._target_output_callback: Optional[Callable[[], Any]] = None

    # === CHANNEL 1: CONVERSATION (User <-> AI Dialogue) ===
    def register_ui_channel(self, log_cb: Callable[[str, str], None]) -> None:
        """Links the presentation layer's log box directly to Channel 1."""
        with self._routing_lock:
            self._ui_log_callback = log_cb
            print("[IO-LAYER] Channel 1: GUI conversation channel successfully registered.")

    def send_to_kanal_1(self, sender: str, message: str) -> None:
        """Routes human or AI text messages safely to the conversation log view."""
        with self._routing_lock:
            callback = self._ui_log_callback
            
        if callback:
            callback(sender, message)
        else:
            print(f"[IO-LAYER] Channel 1 [From: {sender}]: {message}")

    # === CHANNEL 2: INTERACTION (AI <-> Bridge <-> Active Adapter Input) ===
    def register_adapter_channels(self, input_cb: Callable[[Any], None], output_cb: Callable[[], Any]) -> None:
        """Links the active adapter's generic input and output methods straight to Channel 2."""
        with self._routing_lock:
            self._target_input_callback = input_cb
            self._target_output_callback = output_cb
            print("[IO-LAYER] Channel 2: Adapter data matrix interface successfully registered.")

    def send_to_kanal_2(self, payload: Any) -> None:
        """Relays cognitive action payloads or tokens directly to the active app adapter interface."""
        with self._routing_lock:
            callback = self._target_input_callback
            
        if callback:
            # Invoked safely via transaction routing boundaries
            callback(payload)
        else:
            print("[IO-LAYER] Channel 2 Aborted: No active target app receiver allocated.")

    def read_from_kanal_2(self) -> Any:
        """Fetches the current live state matrix or telemetry metrics from the active adapter layer."""
        with self._routing_lock:
            callback = self._target_output_callback
            
        if callback:
            return callback()
        return None

