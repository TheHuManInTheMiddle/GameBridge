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
            "C:\\Program Files\\Notepad++\\notepad++.exe"
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

            subprocess.Popen(
                self.target_path
            )

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

            user32 = ctypes.windll.user32

            user32.FindWindowW.restype = ctypes.c_void_p
            user32.FindWindowW.argtypes = [
                ctypes.c_wchar_p,
                ctypes.c_wchar_p
            ]

            user32.ShowWindow.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int
            ]

            user32.SetForegroundWindow.argtypes = [
                ctypes.c_void_p
            ]

            hwnd = user32.FindWindowW(
                ctypes.c_wchar_p("Notepad++"),
                None
            )

            if hwnd:

                user32.ShowWindow(
                    hwnd,
                    9
                )

                user32.SetForegroundWindow(
                    hwnd
                )

                time.sleep(0.1)

                return True

        except Exception:
            pass

        return False

    def _find_scintilla_window(self):
        """Finds the active Scintilla editor control inside Notepad++."""

        try:

            user32 = ctypes.windll.user32

            user32.FindWindowW.restype = ctypes.c_void_p
            user32.FindWindowW.argtypes = [
                ctypes.c_wchar_p,
                ctypes.c_wchar_p
            ]

            user32.GetClassNameW.restype = ctypes.c_int
            user32.GetClassNameW.argtypes = [
                ctypes.c_void_p,
                ctypes.c_wchar_p,
                ctypes.c_int
            ]

            user32.EnumChildWindows.restype = ctypes.c_bool

            main_hwnd = user32.FindWindowW(
                ctypes.c_wchar_p("Notepad++"),
                None
            )

            if not main_hwnd:
                return None

            scintilla_windows = []

            enum_callback_type = ctypes.WINFUNCTYPE(
                ctypes.c_bool,
                ctypes.c_void_p,
                ctypes.c_void_p
            )

            def enum_child_callback(
                hwnd,
                lparam
            ):
                try:

                    class_name = ctypes.create_unicode_buffer(
                        256
                    )

                    user32.GetClassNameW(
                        hwnd,
                        class_name,
                        256
                    )

                    if class_name.value.lower() == "scintilla":

                        scintilla_windows.append(
                            hwnd
                        )

                except Exception:
                    pass

                return True

            callback = enum_callback_type(
                enum_child_callback
            )

            user32.EnumChildWindows(
                main_hwnd,
                callback,
                0
            )

            if scintilla_windows:

                return scintilla_windows[0]

        except Exception:
            pass

        return None

    def _read_scintilla_text(self):
        """
        Reads the current Scintilla document directly from the
        Notepad++ process using Windows process memory APIs.

        This is telemetry/readback only and does not use:
          - PyAutoGUI
          - clipboard
          - keyboard input
          - Channel 2
        """

        scintilla_hwnd = self._find_scintilla_window()

        if not scintilla_hwnd:

            print(
                f"[{self.adapter_name}] "
                "Scintilla editor control not found."
            )

            return None

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        user32.GetWindowThreadProcessId.restype = ctypes.c_ulong
        user32.GetWindowThreadProcessId.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_ulong)
        ]

        user32.SendMessageW.restype = ctypes.c_ssize_t
        user32.SendMessageW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_size_t,
            ctypes.c_void_p
        ]

        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.OpenProcess.argtypes = [
            ctypes.c_ulong,
            ctypes.c_bool,
            ctypes.c_ulong
        ]

        kernel32.VirtualAllocEx.restype = ctypes.c_void_p
        kernel32.VirtualAllocEx.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_ulong,
            ctypes.c_ulong
        ]

        kernel32.ReadProcessMemory.restype = ctypes.c_bool
        kernel32.ReadProcessMemory.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t)
        ]

        kernel32.VirtualFreeEx.restype = ctypes.c_bool
        kernel32.VirtualFreeEx.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_ulong
        ]

        kernel32.CloseHandle.restype = ctypes.c_bool
        kernel32.CloseHandle.argtypes = [
            ctypes.c_void_p
        ]

        SCI_GETTEXTLENGTH = 2183
        SCI_GETTEXT = 2182

        try:

            process_id = ctypes.c_ulong()

            user32.GetWindowThreadProcessId(
                scintilla_hwnd,
                ctypes.byref(process_id)
            )

            if not process_id.value:

                return None

            PROCESS_VM_OPERATION = 0x0008
            PROCESS_VM_READ = 0x0010
            PROCESS_VM_WRITE = 0x0020
            PROCESS_QUERY_INFORMATION = 0x0400

            process_handle = kernel32.OpenProcess(
                PROCESS_VM_OPERATION
                | PROCESS_VM_READ
                | PROCESS_VM_WRITE
                | PROCESS_QUERY_INFORMATION,
                False,
                process_id.value
            )

            if not process_handle:

                print(
                    f"[{self.adapter_name}] "
                    "Could not open Notepad++ process for telemetry readback."
                )

                return None

            remote_buffer = None

            try:

                text_length = user32.SendMessageW(
                    scintilla_hwnd,
                    SCI_GETTEXTLENGTH,
                    0,
                    None
                )

                if text_length < 0:

                    return None

                buffer_size = int(text_length) + 1

                remote_buffer = kernel32.VirtualAllocEx(
                    process_handle,
                    None,
                    buffer_size,
                    0x1000 | 0x2000,
                    0x04
                )

                if not remote_buffer:

                    print(
                        f"[{self.adapter_name}] "
                        "Could not allocate telemetry readback buffer."
                    )

                    return None

                user32.SendMessageW(
                    scintilla_hwnd,
                    SCI_GETTEXT,
                    buffer_size,
                    remote_buffer
                )

                local_buffer = ctypes.create_string_buffer(
                    buffer_size
                )

                bytes_read = ctypes.c_size_t()

                success = kernel32.ReadProcessMemory(
                    process_handle,
                    remote_buffer,
                    local_buffer,
                    buffer_size,
                    ctypes.byref(bytes_read)
                )

                if not success:

                    print(
                        f"[{self.adapter_name}] "
                        "Could not read Scintilla telemetry buffer."
                    )

                    return None

                raw_text = local_buffer.raw[
                    :bytes_read.value
                ]

                raw_text = raw_text.split(
                    b"\x00",
                    1
                )[0]

                try:

                    return raw_text.decode(
                        "utf-8",
                        errors="replace"
                    )

                except Exception:

                    return raw_text.decode(
                        locale.getpreferredencoding(),
                        errors="replace"
                    )

            finally:

                if remote_buffer:

                    kernel32.VirtualFreeEx(
                        process_handle,
                        remote_buffer,
                        0,
                        0x8000
                    )

                kernel32.CloseHandle(
                    process_handle
                )

        except Exception as e:

            print(
                f"[{self.adapter_name}] "
                f"Scintilla telemetry readback failed: {e}"
            )

            return None

    def read_telemetry(self) -> dict:
        """Returns current runtime state and live Notepad++ text."""

        current_text = self._read_scintilla_text()

        telemetry = {
            "application": "Notepad++",
            "status": "connected",
            "current_context": (
                current_text
                if current_text is not None
                else ""
            ),
            "timestamp": time.time()
        }

        if current_text is None:

            telemetry["telemetry_status"] = (
                "readback_unavailable"
            )

        else:

            telemetry["telemetry_status"] = (
                "readback_ok"
            )

        return telemetry

    def execute_interaction(self, action_data: Any):
        """
        Channel 2 target execution.

        Accepts:
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

                    parsed = json.loads(
                        cleaned_data
                    )

                    if isinstance(
                        parsed,
                        dict
                    ):

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

            if isinstance(
                payload,
                dict
            ):

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

        clean_text_to_type = (
            clean_text_to_type.strip()
        )

        if not clean_text_to_type:

            print(
                f"[{self.adapter_name}] "
                "Channel 2 payload contained no executable text."
            )

            return

        # ---------------------------------------------------------
        # PYAUTOGUI EXECUTION
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