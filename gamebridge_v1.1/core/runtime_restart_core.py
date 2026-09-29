# -*- coding: utf-8 -*-
"""
GameBridge Runtime Restart Core

KOPPLINGAR:
 - HÄMTAS AV:
   - functions/bridge_functions.py
 - PÅVERKAR:
   - GameBridge runtime subsystems
   - AdapterLoader plugin discovery

ANSVAR:
 - Utföra kontrollerad soft reset av GameBridge.
 - Stoppa aktiva runtime-komponenter.
 - Återställa runtime states till startläge.
 - Ladda om plugin discovery.
 - Starta runtime-komponenterna igen.
 - Behålla samma GameBridge-process och core-instanser.

VIKTIGT:
 - Ingen GUI-logik.
 - Ingen subprocess.
 - Ingen processrestart.
 - Inga nya GameBridgeCore-instanser.
"""

import time


class RuntimeRestartCore:

    def __init__(
        self,
        core_parent=None,
        channel_matrix=None,
        runtime_state=None,
        telemetry_worker=None
    ):
        self.core_parent = core_parent
        self.channel_matrix = channel_matrix
        self.runtime_state = runtime_state
        self.telemetry_worker = telemetry_worker

    # ==========================================================
    # SOFT RESET
    # ==========================================================

    def reset_runtime(self):
        """
        Stops active runtime components and restores GameBridge
        runtime state to its default startup condition.
        """

        print(
            "[RUNTIME-RESTART] "
            "Initiating GameBridge soft reset..."
        )

        # ------------------------------------------------------
        # 1. STOP MAIN RUNTIME
        # ------------------------------------------------------

        if self.core_parent:
            self.core_parent.running = False

        # ------------------------------------------------------
        # 2. STOP AI RUNTIME
        # ------------------------------------------------------

        if self.core_parent:

            try:
                self.core_parent.stop_ai_runtime()

            except Exception as exc:
                print(
                    "[RUNTIME-RESTART-WARNING] "
                    f"AI runtime shutdown failed: {exc}"
                )

        # ------------------------------------------------------
        # 3. STOP TELEMETRY
        # ------------------------------------------------------

        if self.telemetry_worker:

            try:
                self.telemetry_worker.running = False

            except Exception:
                pass

            try:
                self.telemetry_worker.set_loop_state(
                    False
                )

            except Exception as exc:
                print(
                    "[RUNTIME-RESTART-WARNING] "
                    f"Telemetry reset failed: {exc}"
                )

        # ------------------------------------------------------
        # 4. DISCONNECT ACTIVE ADAPTER
        # ------------------------------------------------------

        if self.core_parent:

            active_adapter = (
                self.core_parent.active_adapter_instance
            )

            if active_adapter:

                try:
                    active_adapter.shutdown()

                except Exception as exc:
                    print(
                        "[RUNTIME-RESTART-WARNING] "
                        f"Adapter shutdown failed: {exc}"
                    )

                self.core_parent.active_adapter_instance = None

            self.core_parent.current_adapter_folder = "None"

        # ------------------------------------------------------
        # 5. RESET CHANNEL MATRIX
        # ------------------------------------------------------

        if self.channel_matrix:

            self.channel_matrix.update_states(
                False,
                False,
                False,
                False
            )

        # ------------------------------------------------------
        # 6. RESET RUNTIME STATE
        # ------------------------------------------------------

        if self.runtime_state:

            default_states = {
                "ai_active": False,
                "internet_ai_active": False,
                "channel1_active": False,
                "channel2_active": False,
                "telemetry_active": False,
                "locked": False,
                "duplicate_plugin": False,
                "duplicate_plugin_path": None
            }

            for key, value in default_states.items():

                self.runtime_state.set_state(
                    key,
                    value
                )

        # ------------------------------------------------------
        # 7. RESET CORE RUNTIME VALUES
        # ------------------------------------------------------

        if self.core_parent:

            self.core_parent.is_listening = False
            self.core_parent.internet_ai_enabled = False

            self.core_parent.current_adapter_folder = (
                "None"
            )

            self.core_parent.current_voice_hotkey = (
                self.core_parent.global_config.get(
                    "voice_hotkey",
                    "f12"
                ).lower()
            )

        print(
            "[RUNTIME-RESTART] "
            "Runtime state restored to default."
        )

    # ==========================================================
    # PLUGIN REDISCOVERY
    # ==========================================================

    def rediscover_adapters(self):
        """
        Re-scans the plugin tree using the existing AdapterLoader.
        """

        if not self.core_parent:
            return

        loader = getattr(
            self.core_parent,
            "loader",
            None
        )

        if loader is None:
            print(
                "[RUNTIME-RESTART-WARNING] "
                "AdapterLoader is not available."
            )
            return

        print(
            "[RUNTIME-RESTART] "
            "Refreshing plugin discovery..."
        )

        try:

            self.core_parent.available_adapters = (
                loader.discover_and_load()
            )

            print(
                "[RUNTIME-RESTART] "
                "Plugin discovery refreshed."
            )

        except Exception as exc:

            print(
                "[RUNTIME-RESTART-WARNING] "
                "Plugin discovery failed: "
                f"{exc}"
            )

            self.core_parent.available_adapters = {}

    # ==========================================================
    # RESTART
    # ==========================================================

    def restart_runtime(self):
        """
        Performs a complete in-process GameBridge soft reset,
        refreshes plugin discovery, and starts the runtime again.
        """

        self.reset_runtime()

        time.sleep(0.1)

        # ------------------------------------------------------
        # PLUGIN REDISCOVERY
        # ------------------------------------------------------

        self.rediscover_adapters()

        # ------------------------------------------------------
        # START RUNTIME
        # ------------------------------------------------------

        if self.telemetry_worker:

            self.telemetry_worker.running = True

            self.telemetry_worker.set_loop_state(
                False
            )

        if self.core_parent:

            self.core_parent.running = True

            self.core_parent.boot_platform_loops()

        print(
            "[RUNTIME-RESTART] "
            "GameBridge soft reset completed."
        )

        return True