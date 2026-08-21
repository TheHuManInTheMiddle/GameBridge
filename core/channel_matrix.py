# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
 - HÄMTAR FRÅN: Isolerade kärntillstånd (Inga externa logikberoenden).
 - ANROPAS AV: main.py, core/bridge_core.py, functions/router_functions.py, interface/client_gui.py
"""

import threading

class ChannelMatrix:
    def __init__(self):
        # Thread synchronization lock for concurrent matrix evaluation
        self._lock = threading.Lock()
        
        # Synced identification properties across GUI and Bridge Core
        self.channel1_chat_active = False     # Channel 1: Chat / Dialogue
        self.channel2_adapter_active = False  # Channel 2: Target App Interaction
        self.ai_generation_enabled = False    # Master switch for local LLM evaluations
        
        # EXPANSION v3.0: Explicit user-controlled capability for Internet AI (Opt-in)
        self.internet_ai_enabled = False

    def update_states(self, ch1_chat: bool, ch2_adapter: bool, ai_active: bool, internet_active: bool = False) -> None:
        """Transactionally updates the state matrix values from the GUI layer."""
        with self._lock:
            self.channel1_chat_active = ch1_chat
            self.channel2_adapter_active = ch2_adapter
            self.ai_generation_enabled = ai_active
            self.internet_ai_enabled = internet_active
            print(f"[MATRIX-SYNC] States committed -> Ch1: {ch1_chat}, Ch2: {ch2_adapter}, AI Active: {ai_active}, Internet AI: {internet_active}")

    def is_ai_blocked(self) -> bool:
        """Enforces a strict safety barrier check before allowing any LLM inference tokens."""
        with self._lock:
            return not self.ai_generation_enabled

    def is_internet_blocked(self) -> bool:
        """Enforces a strict capability barrier check before allowing external port 8080 routing."""
        with self._lock:
            return not self.internet_ai_enabled

    def should_route_to_chat(self) -> bool:
        """Validates if the computed AI response text is authorized to render in the GUI."""
        with self._lock:
            return self.channel1_chat_active

    def should_route_to_adapter(self, active_instance) -> bool:
        """Validates if automated AI payload dispatches are allowed to mutate the target app."""
        with self._lock:
            return self.channel2_adapter_active and active_instance is not None
