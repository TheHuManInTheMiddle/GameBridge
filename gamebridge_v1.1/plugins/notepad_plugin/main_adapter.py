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
        # Exposed publicly for dynamic frame loader recognition
        self.adapter_name = "Notepad++ (Target X)"
        # FIXED: Relies entirely on PathCore to map the absolute location dynamically
        self.config_path = PathCore.get_adapter_file("notepad_plugin", "plugin_config.json")
        self.target_path = "C:\\Program Files\\Notepad\\notepad++.exe"
        
    def initialize(self):
        """Initializes settings and safely extracts local application executables paths."""
        print(f"[{self.adapter_name}] Initializing reference extension...")
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.target_path = config.get("target_path", self.target_path)
            except Exception as e:
                print(f"[{self.adapter_name}] Configuration processing failure: {e}")

    def boot_or_attach(self):
        """Validates host processes to either connect or spawn a clean execution lifecycle."""
        print(f"[{self.adapter_name}] Evaluating external process lifecycle states...")
        try:
            # DYNAMISK FIX: Använder systemets preferred encoding istället för hårdkodad cp1252
            current_encoding = locale.getpreferredencoding()
            output = subprocess.check_output('tasklist', shell=True).decode(current_encoding, errors='ignore')
            if "notepad++.exe" in output.lower():
                print(f"[{self.adapter_name}] Target process identified as active. Attached to live memory environment.")
                return
        except Exception:
            pass
            
        if os.path.exists(self.target_path):
            print(f"[{self.adapter_name}] Spawning executable instance: {self.target_path}")
            try:
                subprocess.Popen(self.target_path)
                time.sleep(1.5)
            except Exception as e:
                print(f"[{self.adapter_name}] Failed to establish executable frame: {e}")

    def get_capabilities(self) -> dict:
        """Reports automation constraints and system actions dynamically to cognitive layers."""
        return {
            "interaction_type": "active_gui_automation",
            "io_tool": "PyAutoGUI",
            "requires_window_focus": True,
            "supported_actions": ["write_text_cleartext", "simulate_keystrokes"],
            "limitations": "Incapable of dispatching silent or background virtual hardware calls."
        }

    def _focus_target_window(self):
        """Queries local Windows kernel mappings to force screen layer focus."""
        try:
            hwnd = ctypes.windll.user32.FindWindowW(ctypes.c_wchar_p("Notepad++"), None)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                time.sleep(0.1)
                return True
        except Exception:
            pass
        return False

    def read_telemetry(self) -> dict:
        """Extracts runtime environmental properties back into structural system arrays."""
        return {
            "application": "Notepad++",
            "status": "connected",
            "current_context": "Raw text automation frame for physical I/O verification metrics.",
            "timestamp": time.time()
        }

    def execute_interaction(self, action_data: Any):
        """Channel 2 Target: Decodes and drives input parameters directly into the window layer."""
        if not action_data or (isinstance(action_data, str) and "[AI-API-ERROR]" in action_data):
            return
            
        print(f"[{self.adapter_name}] Channel 2 routing execution payload processing...")
        
        intent_map = {}
        if isinstance(action_data, str):
            cleaned_data = action_data.strip()
            if cleaned_data.startswith("{") and cleaned_data.endswith("}"):
                try:
                    intent_map = json.loads(cleaned_data)
                except Exception:
                    pass
        elif isinstance(action_data, dict):
            intent_map = action_data

        clean_text_to_type = ""
        if intent_map:
            clean_text_to_type = intent_map.get("text", "")
            if not clean_text_to_type:
                clean_text_to_type = intent_map.get("command", "")
            
            payload = intent_map.get("payload", {})
            if isinstance(payload, dict):
                decision = payload.get("decision", "")
                if decision:
                    clean_text_to_type = decision

        if not clean_text_to_type and isinstance(action_data, str):
            clean_text_to_type = action_data

        if pyautogui and clean_text_to_type:
            try:
                self._focus_target_window()
                pyautogui.write(f"\n{clean_text_to_type}", interval=0.01)
            except Exception as e:
                print(f"[{self.adapter_name}] PyAutoGUI continuous automated typing exception: {e}")

    def shutdown(self):
        """Flushes local link vectors and disconnects active window focus threads."""
        print(f"[{self.adapter_name}] Safely disconnected automation pipeline hooks.")
