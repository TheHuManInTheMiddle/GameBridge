# -*- coding: utf-8 -*-
"""
CONNECTIONS:
  - FETCHES FROM: adapters/base_adapter.py (Interface blueprint), core/path_core.py
  - CALLED BY: functions/bridge_functions.py
"""

import os
import importlib
import sys
from core.path_core import PathCore

class AdapterLoader:
    def __init__(self, plugin_dir: str = None):
        # FIXED: Relies strictly on the global centralized PathCore if no folder allocation is passed
        if plugin_dir is None:
            self.plugin_dir = PathCore.get_adapter_root()
        else:
            self.plugin_dir = plugin_dir

    def discover_and_load(self) -> dict:
        """Scans subdirectories and registers valid adapters dynamically using global system paths."""
        available_adapters = {}
        
        if not os.path.exists(self.plugin_dir):
            print(f"[LOADER-WARNING] Execution block aborted: Target path does not exist: {self.plugin_dir}")
            return available_adapters

        # Ensure the adapters root directory is officially registered in Python's core search vector
        if self.plugin_dir not in sys.path:
            sys.path.insert(0, self.plugin_dir)

        for folder in os.listdir(self.plugin_dir):
            folder_path = os.path.join(self.plugin_dir, folder)
            
            # Skip hidden directories, caches, or python package configurations
            if not os.path.isdir(folder_path) or folder.startswith("__") or folder.startswith("."):
                continue
                
            main_file = os.path.join(folder_path, "main_adapter.py")
            if not os.path.exists(main_file):
                continue

            try:
                # FIXED: Shifted from absolute hardcoded 'src.adapters' package strings to context-free imports
                # Python now scans folder subdirectories cleanly because self.plugin_dir is injected in sys.path
                module_path = f"{folder}.main_adapter"
                
                # Force reload or clean import to avoid stale tracking references in memory
                if module_path in sys.modules:
                    importlib.reload(sys.modules[module_path])
                module = importlib.import_module(module_path)
                
                # Scan module attributes for a class inheriting from BaseAdapter
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    
                    if isinstance(attribute, type) and attribute_name != "BaseAdapter" and "Adapter" in attribute_name:
                        # Instantiate temporarily to extract the exposed display name
                        temp_instance = attribute()
                        display_name = getattr(temp_instance, "adapter_name", folder)
                        
                        # Safely invoke shutdown on the temp instance if initialized to prevent background memory leaks
                        if hasattr(temp_instance, "shutdown"):
                            try:
                                temp_instance.shutdown()
                            except Exception:
                                pass
                        
                        available_adapters[display_name] = attribute
                        print(f"[LOADER] Discovered and registered extension: '{display_name}' from global tree folder {folder}/")
                        
            except Exception as e:
                print(f"[LOADER-ERROR] Failed to load extension in directory '{folder}': {e}")

        return available_adapters

