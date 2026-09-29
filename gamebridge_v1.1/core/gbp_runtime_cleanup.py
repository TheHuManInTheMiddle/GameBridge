# -*- coding: utf-8 -*-
"""
GBP Runtime Cleanup Core

Cleans stale temporary runtime folders created by GBP plugins.
This core does not load, extract, or execute plugins.
"""

import os
import shutil


class GbpRuntimeCleanupCore:

    @staticmethod
    def cleanup_plugin(plugin_dir: str):
        temp_dir = os.path.join(plugin_dir, "temp")

        if not os.path.isdir(temp_dir):
            return

        try:
            shutil.rmtree(temp_dir)
            print(
                f"[GBP-CLEANUP] Removed runtime temp: {temp_dir}"
            )
        except Exception as e:
            print(
                f"[GBP-CLEANUP] Failed to remove runtime temp "
                f"'{temp_dir}': {e}"
            )

    @classmethod
    def cleanup_all(cls, plugins_root: str):
        if not os.path.isdir(plugins_root):
            return

        for folder in os.listdir(plugins_root):
            plugin_dir = os.path.join(plugins_root, folder)

            if not os.path.isdir(plugin_dir):
                continue

            cls.cleanup_plugin(plugin_dir)