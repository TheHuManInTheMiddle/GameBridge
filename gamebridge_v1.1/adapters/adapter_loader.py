# -*- coding: utf-8 -*-
"""
CONNECTIONS:
  - FETCHES FROM: adapters/base_adapter.py (Interface blueprint), core/path_core.py
  - CALLED BY: functions/bridge_functions.py
"""

import os
import importlib
import importlib.util
import sys
from core.path_core import PathCore
from adapters.gbp_runtime import GbpRuntime
from adapters.base_adapter import BaseAdapter


class AdapterLoader:
    def __init__(
        self,
        plugin_dir: str = None,
        runtime_state=None
    ):
        # FIXED: Relies strictly on the global centralized PathCore if no folder allocation is passed
        if plugin_dir is None:
            self.plugin_dir = PathCore.get_adapter_root()
        else:
            self.plugin_dir = plugin_dir

        # Use the existing central RuntimeStateCore instance.
        # The caller must provide the shared runtime state.
        self.runtime_state = runtime_state

    def discover_and_load(self) -> dict:
        """Scans plugin directories and registers valid adapters dynamically."""
        available_adapters = {}

        if not os.path.exists(self.plugin_dir):
            print(
                f"[LOADER-WARNING] Execution block aborted: "
                f"Target path does not exist: {self.plugin_dir}"
            )
            return available_adapters

        # Ensure the adapters root directory is officially registered in Python's core search vector
        if self.plugin_dir not in sys.path:
            sys.path.insert(0, self.plugin_dir)

        for folder in os.listdir(self.plugin_dir):
            folder_path = os.path.join(self.plugin_dir, folder)

            # Skip hidden directories, caches, or python package configurations
            if (
                not os.path.isdir(folder_path)
                or folder.startswith("__")
                or folder.startswith(".")
            ):
                continue

            # Plugin folders may contain either the unpacked .py representation,
            # a packed .gbp representation, or both.
            gbp_files = [
                filename
                for filename in os.listdir(folder_path)
                if filename.lower().endswith(".gbp")
            ]

            main_file = os.path.join(
                folder_path,
                "main_adapter.py"
            )

            packed_plugin = False

            # One-shot duplicate detection.
            # If a plugin contains both representations, record the first
            # duplicate in RuntimeStateCore. The discovery process continues.
            if (
                os.path.exists(main_file)
                and gbp_files
                and self.runtime_state is not None
                and not self.runtime_state.get_state(
                    "duplicate_plugin",
                    False
                )
            ):
                self.runtime_state.set_state(
                    "duplicate_plugin",
                    True
                )

                self.runtime_state.set_state(
                    "duplicate_plugin_path",
                    folder_path
                )

                print(
                    f"[LOADER-WARNING] Duplicate plugin representation "
                    f"detected in '{folder_path}' "
                    f"({len(gbp_files)} .gbp file(s) + main_adapter.py)."
                )

            if not os.path.exists(main_file):
                if gbp_files:
                    try:
                        gbp_path = os.path.join(
                            folder_path,
                            gbp_files[0]
                        )

                        runtime_dir = GbpRuntime.prepare_plugin(
                            folder_path,
                            gbp_path
                        )

                        main_file = GbpRuntime.get_main_adapter(
                            runtime_dir
                        )

                        packed_plugin = True

                        print(
                            f"[LOADER] Packed plugin '{folder}' "
                            f"prepared from {gbp_files[0]}"
                        )

                    except Exception as e:
                        print(
                            f"[LOADER-ERROR] Failed to prepare packed plugin "
                            f"in directory '{folder}': {e}"
                        )

                        continue

                else:
                    continue

            try:
                if packed_plugin:
                    module_name = (
                        f"gamebridge_packed_{folder}_main_adapter"
                    )

                    spec = importlib.util.spec_from_file_location(
                        module_name,
                        main_file
                    )

                    if spec is None or spec.loader is None:
                        raise ImportError(
                            f"Could not create module specification "
                            f"for packed plugin '{folder}'"
                        )

                    module = importlib.util.module_from_spec(
                        spec
                    )

                    sys.modules[
                        module_name
                    ] = module

                    spec.loader.exec_module(
                        module
                    )

                else:
                    # FIXED: Shifted from absolute hardcoded 'src.adapters' package strings
                    # to context-free imports.
                    module_path = f"{folder}.main_adapter"

                    # Force reload or clean import to avoid stale tracking references in memory
                    if module_path in sys.modules:
                        importlib.reload(
                            sys.modules[module_path]
                        )

                    module = importlib.import_module(
                        module_path
                    )

                # Scan module attributes for a class inheriting from BaseAdapter
                for attribute_name in dir(module):
                    attribute = getattr(
                        module,
                        attribute_name
                    )

                    if (
                        isinstance(attribute, type)
                        and issubclass(attribute, BaseAdapter)
                        and attribute is not BaseAdapter
                    ):
                        # Instantiate temporarily to extract the exposed display name
                        temp_instance = attribute()

                        display_name = getattr(
                            temp_instance,
                            "adapter_name",
                            folder
                        )

                        # Safely invoke shutdown on the temp instance
                        # if initialized to prevent background memory leaks
                        if hasattr(
                            temp_instance,
                            "shutdown"
                        ):
                            try:
                                temp_instance.shutdown()
                            except Exception:
                                pass

                        available_adapters[
                            display_name
                        ] = attribute

                        print(
                            f"[LOADER] Discovered and registered extension: "
                            f"'{display_name}' from global tree folder {folder}/"
                        )

            except Exception as e:
                print(
                    f"[LOADER-ERROR] Failed to load extension "
                    f"in directory '{folder}': {e}"
                )

        return available_adapters