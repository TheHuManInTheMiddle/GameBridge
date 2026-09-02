# -*- coding: utf-8 -*-
"""
CONNECTIONS:
- FETCHES FROM: Isolated core routing (No external application dependencies).
- CALLED BY: main.py, core/channel_matrix.py, functions/router_functions.py
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

        # Monitor: Optional presentation of Channel 2 traffic
        self._monitor_callback: Optional[Callable[[str], None]] = None

    # ==========================================================
    # CHANNEL 1: CONVERSATION
    # ==========================================================

    def register_ui_channel(
        self,
        log_cb: Callable[[str, str], None]
    ) -> None:
        """Links the presentation layer's log box directly to Channel 1."""
        with self._routing_lock:
            self._ui_log_callback = log_cb

            print(
                "[IO-LAYER] Channel 1: GUI conversation "
                "channel successfully registered."
            )

    def send_to_kanal_1(
        self,
        sender: str,
        message: str
    ) -> None:
        """Routes human or AI text messages safely to the conversation log view."""
        with self._routing_lock:
            callback = self._ui_log_callback

            if callback:
                callback(sender, message)
            else:
                print(
                    f"[IO-LAYER] Channel 1 "
                    f"[From: {sender}]: {message}"
                )

    # ==========================================================
    # CHANNEL 2: TARGET APPLICATION
    # ==========================================================

    def register_adapter_channels(
        self,
        input_cb: Callable[[Any], None],
        output_cb: Callable[[], Any]
    ) -> None:
        """Links the active adapter's generic input and output methods to Channel 2."""
        with self._routing_lock:
            self._target_input_callback = input_cb
            self._target_output_callback = output_cb

            print(
                "[IO-LAYER] Channel 2: Adapter data matrix "
                "interface successfully registered."
            )

    def send_to_kanal_2(
        self,
        payload: Any
    ) -> None:
        """
        Relays the raw Channel 2 payload to the active adapter.

        Channel 2 traffic is never routed to Channel 1.

        If the Channel 2 monitor is registered, the same outbound
        payload is also exposed to the diagnostic monitor.
        """
        with self._routing_lock:
            callback = self._target_input_callback
            monitor_callback = self._monitor_callback

            if callback:
                # Primary Channel 2 dispatch
                callback(payload)

                # Optional Channel 2 monitoring.
                # This does not affect Channel 1.
                if monitor_callback:
                    monitor_callback(
                        f"[CHANNEL 2 OUT] {payload}"
                    )

            else:
                print(
                    "[IO-LAYER] Channel 2 Aborted: "
                    "No active target app receiver allocated."
                )

    def read_from_kanal_2(
        self
    ) -> Any:
        """Fetches current live telemetry from the active adapter layer."""
        with self._routing_lock:
            callback = self._target_output_callback

            if callback:
                return callback()

            return None

    # ==========================================================
    # CHANNEL 2 MONITOR
    # ==========================================================

    def register_monitor_channel(
        self,
        monitor_cb: Callable[[str], None]
    ) -> None:
        """Links the Channel 2 diagnostic monitor to the presentation layer."""
        with self._routing_lock:
            self._monitor_callback = monitor_cb

            print(
                "[IO-LAYER] Monitor Channel: Diagnostic "
                "monitoring core vector successfully bound."
            )

    def send_to_monitor(
        self,
        message: str
    ) -> None:
        """Pushes diagnostic or telemetry information to the monitor."""
        with self._routing_lock:
            callback = self._monitor_callback

            if callback:
                callback(message)