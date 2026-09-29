# -*- coding: utf-8 -*-
"""
GameBridge GBP Runtime

PURPOSE:
  - Extracts .gbp plugin packages into the plugin's local temp directory.
  - Makes bundled plugin libraries available to Python.
  - Does not install packages with pip.

RUNTIME STRUCTURE:
  plugins/
    notepad_plugin/
      notepad_plugin.gbp
      plugin_config.json
      plugin_prompt.txt
      temp/
        main_adapter.py
        lib/
        dependencies/
        assets/

The permanent plugin directory remains clean.
"""

import os
import sys
import zipfile


class GbpRuntime:

    @staticmethod
    def get_temp_dir(plugin_dir: str) -> str:
        """
        Returns the local runtime directory for a plugin.
        """
        return os.path.join(
            plugin_dir,
            "temp"
        )

    @staticmethod
    def prepare_plugin(
        plugin_dir: str,
        gbp_path: str
    ) -> str:
        """
        Extracts a .gbp package into the plugin's local
        temp runtime directory.

        Returns:
            Absolute path to the extracted runtime directory.

        Raises:
            FileNotFoundError
            ValueError
            RuntimeError
        """

        plugin_dir = os.path.abspath(
            plugin_dir
        )

        gbp_path = os.path.abspath(
            gbp_path
        )

        if not os.path.exists(gbp_path):
            raise FileNotFoundError(
                f"GBP package not found: {gbp_path}"
            )

        if not zipfile.is_zipfile(gbp_path):
            raise ValueError(
                f"Invalid GBP package: {gbp_path}"
            )

        temp_dir = GbpRuntime.get_temp_dir(
            plugin_dir
        )

        os.makedirs(
            temp_dir,
            exist_ok=True
        )

        try:
            with zipfile.ZipFile(
                gbp_path,
                "r"
            ) as archive:

                # Protect against ZIP path traversal.
                temp_root = os.path.realpath(
                    temp_dir
                )

                for member in archive.infolist():

                    member_path = os.path.realpath(
                        os.path.join(
                            temp_dir,
                            member.filename
                        )
                    )

                    if not (
                        member_path == temp_root
                        or member_path.startswith(
                            temp_root + os.sep
                        )
                    ):
                        raise ValueError(
                            "Unsafe path detected in GBP package: "
                            f"{member.filename}"
                        )

                archive.extractall(
                    temp_dir
                )

        except Exception:
            if os.path.isdir(temp_dir):
                import shutil

                shutil.rmtree(
                    temp_dir,
                    ignore_errors=True
                )

            raise

        main_adapter = os.path.join(
            temp_dir,
            "main_adapter.py"
        )

        if not os.path.isfile(
            main_adapter
        ):
            if os.path.isdir(temp_dir):
                import shutil

                shutil.rmtree(
                    temp_dir,
                    ignore_errors=True
                )

            raise ValueError(
                "GBP package does not contain "
                "main_adapter.py"
            )

        GbpRuntime._register_runtime_paths(
            temp_dir
        )

        print(
            f"[GBP-RUNTIME] Loaded package: "
            f"{os.path.basename(gbp_path)}"
        )

        print(
            f"[GBP-RUNTIME] Runtime path: "
            f"{temp_dir}"
        )

        return temp_dir

    @staticmethod
    def _register_runtime_paths(
        runtime_dir: str
    ) -> None:
        """
        Makes the plugin runtime and its bundled library
        directories available to Python.

        No pip installation is performed.
        """

        paths = [
            runtime_dir,
            os.path.join(
                runtime_dir,
                "lib"
            ),
            os.path.join(
                runtime_dir,
                "dependencies"
            )
        ]

        for path in paths:

            if (
                os.path.isdir(path)
                and path not in sys.path
            ):
                sys.path.insert(
                    0,
                    path
                )

                print(
                    f"[GBP-RUNTIME] Python path added: "
                    f"{path}"
                )

    @staticmethod
    def get_main_adapter(
        runtime_dir: str
    ) -> str:
        """
        Returns the extracted main_adapter.py path.
        """
        return os.path.join(
            runtime_dir,
            "main_adapter.py"
        )