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
 - Fungerar både vid vanlig Python-körning och som PyInstaller .exe.
 - Externa runtime-mappar ligger bredvid main.exe.
 - Ingen affärslogik.
 - Ingen AI-logik.
 - Ingen providerlogik.
 - Inga hårdkodade projektsökvägar.

EXTERN RUNTIME-STRUKTUR:

    GameBridge/
    ├── config/
    ├── plugins/
    ├── providers/
    ├── assets/
    └── main.py

    eller efter PyInstaller:

    dist/main/
    ├── main.exe
    ├── config/
    ├── plugins/
    ├── providers/
    └── assets/
"""

import os
import sys


class PathCore:

    # ------------------------------------------------------------------
    # PROJECT / RUNTIME ROOT
    # ------------------------------------------------------------------

    if getattr(sys, "frozen", False):
        # PyInstaller:
        # Använd mappen där den körbara filen faktiskt ligger.
        #
        # Detta gör att externa mappar som config/, plugins/,
        # providers/ och assets/ ligger bredvid main.exe.
        PROJECT_ROOT = os.path.dirname(
            os.path.abspath(sys.executable)
        )

    else:
        # Vanlig Python-körning:
        # core/path_core.py ligger en nivå under projektroten.
        _CORE_DIR = os.path.dirname(
            os.path.abspath(__file__)
        )

        PROJECT_ROOT = os.path.dirname(
            _CORE_DIR
        )

    # ------------------------------------------------------------------
    # GENERELL SÖKVÄG
    # ------------------------------------------------------------------

    @classmethod
    def get_absolute_path(
        cls,
        *paths: str
    ) -> str:
        """
        Kombinerar sökvägar till en garanterad absolut sökväg.

        Alla externa GameBridge-resurser ska byggas genom denna metod.
        """

        return os.path.abspath(
            os.path.join(
                cls.PROJECT_ROOT,
                *paths
            )
        )

    # ------------------------------------------------------------------
    # CONFIG
    # ------------------------------------------------------------------

    @classmethod
    def get_config_path(
        cls,
        filename: str = "settings.json"
    ) -> str:
        """
        Returnerar absolut sökväg till en fil i config/.
        """

        return cls.get_absolute_path(
            "config",
            filename
        )

    # ------------------------------------------------------------------
    # PLUGINS / ADAPTERS
    # ------------------------------------------------------------------

    @classmethod
    def get_adapter_root(cls) -> str:
        """
        Returnerar absolut sökväg till plugin-/adapter-sfären.
        """

        return cls.get_absolute_path(
            "plugins"
        )

    @classmethod
    def get_adapter_file(
        cls,
        adapter_folder: str,
        filename: str
    ) -> str:
        """
        Returnerar absolut sökväg till en fil i ett specifikt
        plugin-/adapterpaket.
        """

        return cls.get_absolute_path(
            "plugins",
            adapter_folder,
            filename
        )

    # ------------------------------------------------------------------
    # PROVIDERS
    # ------------------------------------------------------------------

    @classmethod
    def get_provider_root(cls) -> str:
        """
        Returnerar absolut sökväg till den externa providers/-mappen.

        Providerfilerna ligger utanför den paketerade kärnan och
        ska därför kunna bytas eller läggas till utan att GameBridge
        behöver byggas om.
        """

        return cls.get_absolute_path(
            "providers"
        )

    # ------------------------------------------------------------------
    # ASSETS
    # ------------------------------------------------------------------

    @classmethod
    def get_asset_path(
        cls,
        filename: str
    ) -> str:
        """
        Returnerar absolut sökväg till en extern asset.
        """

        return cls.get_absolute_path(
            "assets",
            filename
        )

    # ------------------------------------------------------------------
    # ENVIRONMENT
    # ------------------------------------------------------------------

    @classmethod
    def get_env_path(cls) -> str:
        """
        Returnerar absolut sökväg till GameBridges externa .env-fil.
        """

        return cls.get_absolute_path(
            ".env"
        )

    # ------------------------------------------------------------------
    # LOGGING
    # ------------------------------------------------------------------

    @classmethod
    def get_internet_log_path(cls) -> str:
        """
        Returnerar absolut sökväg till GameBridges append-only-logg
        för internetförfrågningar.
        """

        return cls.get_absolute_path(
            "logs",
            "internet_queries.jsonl"
        )