# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
  - HÄMTAR FRÅN: adapters.base_adapter, core.path_core
  - ANROPAS AV: adapters.adapter_loader (Dynamisk plugin-skanner under runtime)
"""

import os
import json
import subprocess
import time
import ctypes
import locale
from typing import Any

from adapters.base_adapter import BaseAdapter
from core.path_core import PathCore


try:
    import pyautogui

    pyautogui.FAILSAFE = True

except ImportError:
    pyautogui = None


class NotepadAdapter(BaseAdapter):

    def __init__(self):
        super().__init__()

        self.adapter_name = "Notepad++ (Target X)"

        self.config_path = PathCore.get_adapter_file(
            "notepad_plugin",
            "plugin_config.json"
        )

        self.target_path = (
            "C:\\Program Files\\Notepad\\notepad++.exe"
        )

    def initialize(self):
        """Initializes settings and safely extracts local application executable paths."""

        print(
            f"[{self.adapter_name}] "
            "Initializing reference extension..."
        )

        if not os.path.exists(self.config_path):
            return

        try:
            with open(
                self.config_path,
                "r",
                encoding="utf-8"
            ) as f:

                config = json.load(f)

            self.target_path = config.get(
                "target_path",
                self.target_path
            )

        except Exception as e:

            print(
                f"[{self.adapter_name}] "
                f"Configuration processing failure: {e}"
            )

    def boot_or_attach(self):
        """Validates host processes and either attaches or starts Notepad++."""

        print(
            f"[{self.adapter_name}] "
            "Evaluating external process lifecycle states..."
        )

        try:
            current_encoding = locale.getpreferredencoding()

            output = subprocess.check_output(
                "tasklist",
                shell=True
            ).decode(
                current_encoding,
                errors="ignore"
            )

            if "notepad++.exe" in output.lower():

                print(
                    f"[{self.adapter_name}] "
                    "Target process identified as active. "
                    "Attached to live memory environment."
                )

                return

        except Exception:
            pass

        if not os.path.exists(self.target_path):
            print(
                f"[{self.adapter_name}] "
                f"Executable not found: {self.target_path}"
            )
            return

        print(
            f"[{self.adapter_name}] "
            f"Spawning executable instance: {self.target_path}"
        )

        try:
            subprocess.Popen(self.target_path)
            time.sleep(1.5)

        except Exception as e:

            print(
                f"[{self.adapter_name}] "
                f"Failed to establish executable frame: {e}"
            )

    def get_capabilities(self) -> dict:
        """Reports automation constraints and supported actions."""

        return {
            "interaction_type": "active_gui_automation",
            "io_tool": "PyAutoGUI",
            "requires_window_focus": True,
            "supported_actions": [
                "write_text_cleartext",
                "simulate_keystrokes"
            ],
            "limitations": (
                "Incapable of dispatching silent or background "
                "virtual hardware calls."
            )
        }

    def _focus_target_window(self):
        """Brings the Notepad++ window to the foreground."""

        try:
            hwnd = ctypes.windll.user32.FindWindowW(
                ctypes.c_wchar_p("Notepad++"),
                None
            )

            if hwnd:

                ctypes.windll.user32.ShowWindow(
                    hwnd,
                    9
                )

                ctypes.windll.user32.SetForegroundWindow(
                    hwnd
                )

                time.sleep(0.1)

                return True

        except Exception:
            pass

        return False

    def read_telemetry(self) -> dict:
        """Returns current runtime state for the routing layer."""

        return {
            "application": "Notepad++",
            "status": "connected",
            "current_context": (
                "Raw text automation frame for "
                "physical I/O verification metrics."
            ),
            "timestamp": time.time()
        }

    def execute_interaction(self, action_data: Any):
        """
        Channel 2 target execution.

        Accepts either:
          - JSON string
          - Python dictionary
          - Plain text fallback

        Only the resulting text payload is written into
        the focused Notepad++ window.
        """

        if not action_data:
            return

        if (
            isinstance(action_data, str)
            and "[AI-API-ERROR]" in action_data
        ):
            return

        print(
            f"[{self.adapter_name}] "
            "Channel 2 routing execution payload processing..."
        )

        intent_map = {}

        # ---------------------------------------------------------
        # JSON STRING
        # ---------------------------------------------------------

        if isinstance(action_data, str):

            cleaned_data = action_data.strip()

            if (
                cleaned_data.startswith("{")
                and cleaned_data.endswith("}")
            ):

                try:
                    parsed = json.loads(cleaned_data)

                    if isinstance(parsed, dict):
                        intent_map = parsed

                except Exception as e:

                    print(
                        f"[{self.adapter_name}] "
                        f"JSON payload parsing failed: {e}"
                    )

        # ---------------------------------------------------------
        # DIRECT DICTIONARY
        # ---------------------------------------------------------

        elif isinstance(action_data, dict):

            intent_map = action_data

        # ---------------------------------------------------------
        # EXTRACT TEXT PAYLOAD
        # ---------------------------------------------------------

        clean_text_to_type = ""

        if intent_map:

            clean_text_to_type = intent_map.get(
                "text",
                ""
            )

            if not clean_text_to_type:

                clean_text_to_type = intent_map.get(
                    "command",
                    ""
                )

            payload = intent_map.get(
                "payload",
                {}
            )

            if isinstance(payload, dict):

                decision = payload.get(
                    "decision",
                    ""
                )

                if decision:
                    clean_text_to_type = decision

        # ---------------------------------------------------------
        # PLAIN TEXT FALLBACK
        # ---------------------------------------------------------

        if (
            not clean_text_to_type
            and isinstance(action_data, str)
        ):

            clean_text_to_type = action_data

        if not isinstance(
            clean_text_to_type,
            str
        ):

            clean_text_to_type = str(
                clean_text_to_type
            )

        clean_text_to_type = clean_text_to_type.strip()

        if not clean_text_to_type:
            print(
                f"[{self.adapter_name}] "
                "Channel 2 payload contained no executable text."
            )
            return

        # ---------------------------------------------------------
        # PYAutoGUI EXECUTION
        # ---------------------------------------------------------

        if pyautogui is None:

            print(
                f"[{self.adapter_name}] "
                "PyAutoGUI unavailable. "
                "Channel 2 execution aborted."
            )

            return

        try:

            focused = self._focus_target_window()

            if not focused:

                print(
                    f"[{self.adapter_name}] "
                    "Could not focus Notepad++ window."
                )

                return

            pyautogui.write(
                f"\n{clean_text_to_type}",
                interval=0.01
            )

            print(
                f"[{self.adapter_name}] "
                "Channel 2 payload executed successfully."
            )

        except Exception as e:

            print(
                f"[{self.adapter_name}] "
                f"PyAutoGUI continuous automated typing exception: {e}"
            )

    def shutdown(self):
        """Safely disconnects the automation pipeline."""

        print(
            f"[{self.adapter_name}] "
            "Safely disconnected automation pipeline hooks."
        )