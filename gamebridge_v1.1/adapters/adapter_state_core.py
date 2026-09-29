# -*- coding: utf-8 -*-
"""
CONNECTIONS:
  - FETCHES FROM: core/path_core.py, config/adapter_apps.json
  - CALLED BY: functions/bridge_functions.py

RESPONSIBILITY:
  - Manage adapter plugin_config.json target path.
  - Create plugin_config.json when missing.
  - Read existing target_path.
  - Open the Windows file picker when target_path is missing
    or no longer points to an existing file.
  - Preserve existing plugin configuration fields.
"""

import json
import os
import tkinter as tk
from tkinter import filedialog

from core.path_core import PathCore


class AdapterStateCore:
    """Handles adapter target configuration and target application selection."""

    def __init__(self):
        self.adapter_apps_config_path = PathCore.get_config_path(
            "adapter_apps.json"
        )

    def get_plugin_config_path(self, adapter_folder: str) -> str:
        """Return the absolute path to the adapter's plugin_config.json."""

        return PathCore.get_adapter_file(
            adapter_folder,
            "plugin_config.json"
        )

    def load_plugin_config(self, adapter_folder: str) -> dict:
        """Load an adapter's plugin configuration safely."""

        config_path = self.get_plugin_config_path(
            adapter_folder
        )

        if not os.path.exists(config_path):
            return {}

        try:
            with open(
                config_path,
                "r",
                encoding="utf-8"
            ) as f:
                config = json.load(f)

            if isinstance(config, dict):
                return config

        except Exception as e:
            print(
                "[ADAPTER-STATE] "
                f"Failed to load plugin configuration: {e}"
            )

        return {}

    def save_plugin_config(
        self,
        adapter_folder: str,
        config: dict
    ) -> bool:
        """Persist an adapter's plugin configuration."""

        config_path = self.get_plugin_config_path(
            adapter_folder
        )

        config_dir = os.path.dirname(
            config_path
        )

        try:
            os.makedirs(
                config_dir,
                exist_ok=True
            )

            with open(
                config_path,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    config,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            return True

        except Exception as e:
            print(
                "[ADAPTER-STATE] "
                f"Failed to save plugin configuration: {e}"
            )

            return False

    def load_supported_extensions(self) -> list:
        """Load supported target application extensions."""

        if not os.path.exists(
            self.adapter_apps_config_path
        ):
            print(
                "[ADAPTER-STATE] "
                "adapter_apps.json not found."
            )

            return []

        try:
            with open(
                self.adapter_apps_config_path,
                "r",
                encoding="utf-8"
            ) as f:
                config = json.load(f)

            extensions = config.get(
                "extensions",
                []
            )

            if not isinstance(
                extensions,
                list
            ):
                return []

            normalized = []

            for extension in extensions:
                extension = str(
                    extension
                ).strip().lower()

                if not extension:
                    continue

                if not extension.startswith("."):
                    extension = "." + extension

                normalized.append(
                    extension
                )

            return normalized

        except Exception as e:
            print(
                "[ADAPTER-STATE] "
                f"Failed to load adapter application types: {e}"
            )

            return []

    def select_target_application(self) -> str:
        """Open the Windows file picker for a supported target application."""

        extensions = self.load_supported_extensions()

        if not extensions:
            print(
                "[ADAPTER-STATE] "
                "No supported target application types configured."
            )

            return ""

        patterns = " ".join(
            f"*{extension}"
            for extension in extensions
        )

        filetypes = [
            (
                "Supported target applications",
                patterns
            ),
            (
                "All files",
                "*.*"
            )
        ]

        root = tk.Tk()
        root.withdraw()
        root.attributes(
            "-topmost",
            True
        )

        try:
            selected_path = filedialog.askopenfilename(
                title="Select target application",
                filetypes=filetypes
            )

        finally:
            root.destroy()

        return selected_path or ""

    def resolve_target_path(
        self,
        adapter_folder: str
    ) -> str:
        """
        Resolve an adapter's target application path.

        Creates plugin_config.json when necessary.
        Opens the file picker when target_path is missing
        or points to a file that no longer exists.
        """

        config = self.load_plugin_config(
            adapter_folder
        )

        target_path = str(
            config.get(
                "target_path",
                ""
            )
        ).strip()

        if target_path and os.path.isfile(
            target_path
        ):
            return target_path

        selected_path = self.select_target_application()

        if not selected_path:
            print(
                "[ADAPTER-STATE] "
                "No target application selected."
            )

            return ""

        config["target_path"] = selected_path

        if not self.save_plugin_config(
            adapter_folder,
            config
        ):
            return ""

        print(
            "[ADAPTER-STATE] "
            f"Target application configured: {selected_path}"
        )

        return selected_path