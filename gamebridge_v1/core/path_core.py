# -*- coding: utf-8 -*-
"""
GameBridge Path Core

KOPPLINGAR:
 - ANROPAS AV:
     - GameBridge-ramverket och övriga core-funktioner
 - ANVÄNDS AV:
     - ai.internet_transport.InternetTransport

ANSVAR:
 - Centraliserad och absolut sökvägshantering.
 - Ingen affärslogik.
 - Ingen AI-logik.
 - Ingen providerlogik.
 - Inga hårdkodade projektsökvägar.
"""

import os


class PathCore:
    # core/path_core.py ligger en nivå under projektroten.
    _CORE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(_CORE_DIR)

    @classmethod
    def get_absolute_path(cls, *paths: str) -> str:
        """Kombinerar sökvägar till en garanterad absolut sökväg."""
        return os.path.abspath(
            os.path.join(cls.PROJECT_ROOT, *paths)
        )

    @classmethod
    def get_config_path(
        cls,
        filename: str = "settings.json"
    ) -> str:
        """Returnerar absolut sökväg till global konfiguration."""
        return cls.get_absolute_path(
            "config",
            filename
        )

    @classmethod
    def get_adapter_root(cls) -> str:
        """Returnerar absolut sökväg till plugin-sfären."""
        return cls.get_absolute_path(
            "plugins"
        )

    @classmethod
    def get_adapter_file(
        cls,
        adapter_folder: str,
        filename: str
    ) -> str:
        """Returnerar absolut sökväg till en plugin-konfigurationsfil."""
        return cls.get_absolute_path(
            "plugins",
            adapter_folder,
            filename
        )

    @classmethod
    def get_internet_log_path(cls) -> str:
        """
        Returnerar absolut sökväg till GameBridges
        append-only-logg för internetförfrågningar.
        """
        return cls.get_absolute_path(
            "logs",
            "internet_queries.jsonl"
        )
