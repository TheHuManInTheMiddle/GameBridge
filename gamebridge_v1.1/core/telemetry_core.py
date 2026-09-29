# -*- coding: utf-8 -*-
"""
CONNECTIONS:
- FETCHES FROM: core/io_layer.py
- CALLED BY: main/main.py, interface/client_gui.py, AI runtime

ANSVAR:
- Hantera telemetry-tillstånd.
- Tillåta eller neka telemetry-läsning.
- Leverera aktuell telemetry på uttrycklig begäran.
- Ingen bakgrundspolling.
- Ingen GUI-logik.
- Ingen AI-logik.
"""

import threading


class TelemetryCore:
    def __init__(self, io_layer=None):
        self.io_layer = io_layer
        self.loop_active = False
        self.running = True
        self._lock = threading.Lock()

    # ==========================================================
    # TELEMETRY PERMISSION
    # ==========================================================

    def set_loop_state(self, active: bool) -> None:
        """
        Sets the telemetry permission state.

        This no longer controls a background polling loop.
        The state only determines whether telemetry requests
        are currently permitted.
        """
        with self._lock:
            self.loop_active = bool(active)

            print(
                "[TELEMETRY-CORE] Telemetry permission "
                f"set to: {self.loop_active}"
            )

    def pause(self) -> None:
        """
        Disables telemetry requests.

        Kept as a compatibility interface for the existing GUI.
        """
        self.set_loop_state(False)

        print(
            "[TELEMETRY-CORE] Telemetry requests disabled."
        )

    def resume(self) -> None:
        """
        Enables telemetry requests.

        Kept as a compatibility interface for the existing GUI.
        No worker or polling thread is created.
        """
        with self._lock:

            if not self.running:

                print(
                    "[TELEMETRY-CORE] Telemetry enable request "
                    "ignored: core is terminated."
                )

                return

            self.loop_active = True

        print(
            "[TELEMETRY-CORE] Telemetry requests enabled."
        )

    # ==========================================================
    # TELEMETRY REQUEST
    # ==========================================================

    def request_telemetry(self):
        """
        Performs exactly one telemetry read when telemetry is enabled.

        No polling loop is created.
        No delay is introduced.
        No GUI callback is triggered.

        Returns:
            Current telemetry data, or None when telemetry is
            disabled or no I/O layer is available.
        """

        with self._lock:

            if not self.running:

                print(
                    "[TELEMETRY-CORE] Telemetry request denied: "
                    "core is terminated."
                )

                return None

            if not self.loop_active:

                print(
                    "[TELEMETRY-CORE] Telemetry request denied: "
                    "telemetry is disabled."
                )

                return None

            io_layer = self.io_layer

        if not io_layer:

            print(
                "[TELEMETRY-CORE] Telemetry request denied: "
                "no I/O layer is registered."
            )

            return None

        try:

            telemetry_data = (
                io_layer.read_from_kanal_2()
            )

            if telemetry_data is not None:

                print(
                    "[TELEMETRY-CORE] Telemetry request "
                    "completed."
                )

            else:

                print(
                    "[TELEMETRY-CORE] Telemetry request returned "
                    "no data."
                )

            return telemetry_data

        except Exception as exc:

            print(
                "[TELEMETRY-CORE-ERROR] Telemetry request "
                f"failed: {exc}"
            )

            return None

    # ==========================================================
    # STATUS
    # ==========================================================

    def status(self) -> dict:
        """
        Returns the current telemetry permission and lifecycle state.
        """

        with self._lock:

            return {
                "running": self.running,
                "loop_active": self.loop_active,
                "state": (
                    "ENABLED"
                    if self.loop_active
                    else "DISABLED"
                )
            }

    # ==========================================================
    # LEGACY POLLING ENTRY POINT
    # ==========================================================

    def start_polling_worker(
        self,
        current_adapter_callback=None,
        success_ui_callback=None
    ) -> None:
        """
        Compatibility entry point for the current main.py.

        Telemetry no longer uses a background polling worker.

        This function intentionally does nothing except report that
        the legacy polling request has been disabled.
        """

        print(
            "[TELEMETRY-CORE] Background telemetry polling "
            "is disabled. Telemetry is request-driven."
        )