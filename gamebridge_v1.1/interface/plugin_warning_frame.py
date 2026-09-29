# -*- coding: utf-8 -*-

"""
GameBridge Plugin Warning Frame

KOPPLINGAR:
  - HÄMTAR FRÅN:
    - core/runtime_state_core.py
    - interface/plugin_warning_presenter.py
    - functions/bridge_functions.py

ANSVAR:
  - Vara funktionell ram för plugin-varningen.
  - Visa PluginWarningPresenter.
  - Äga funktionella knappar och callbacks.
  - Öppna den aktuella plugin-mappen.
  - Begära soft reset av GameBridge.

VIKTIGT:
  - Presenter äger presentationen.
  - Frame äger funktionaliteten.
  - Frame äger layout och 5 px presentationram.
  - Ingen adapter-loader-logik här.
  - Ingen runtime-state-logik här.
  - Ingen HTML-layout här.
  - Ingen processrestart här.
"""


import os
import subprocess

import customtkinter as ctk

from interface.plugin_warning_presenter import (
    PluginWarningPresenter
)


class PluginWarningFrame(ctk.CTkFrame):

    def __init__(
        self,
        master,
        runtime_state=None,
        core_hub=None,
        localizer=None,
        **kwargs
    ):
        """
        Skapar den funktionella ramen
        för plugin-varningen.
        """

        super().__init__(
            master,
            fg_color="transparent",
            **kwargs
        )

        self.runtime_state = runtime_state
        self.core_hub = core_hub
        self.localizer = localizer

        # ======================================================
        # PRESENTATION GEOMETRY
        # ======================================================

        self.presentation_width = 560
        self.presentation_height = 315

        self.presentation_border = 5

        self.presentation_frame_width = (
            self.presentation_width
            + (self.presentation_border * 2)
        )

        self.presentation_frame_height = (
            self.presentation_height
            + (self.presentation_border * 2)
        )

        self._build_components()

    # ==========================================================
    # LOCALIZATION
    # ==========================================================

    def _get_text(
        self,
        key,
        fallback=""
    ):
        """
        Hämtar lokaliserad text.

        Fallback används endast om localizer saknas
        eller inte hittar nyckeln.
        """

        if not self.localizer:
            return fallback

        try:

            value = self.localizer.get_text(
                key
            )

            if value:
                return str(value)

        except Exception as e:

            print(
                "[PLUGIN-WARNING-LOCALIZER] "
                f"Failed to resolve '{key}': {e}"
            )

        return fallback

    # ==========================================================
    # COMPONENT BUILD
    # ==========================================================

    def _build_components(self):
        """
        Bygger hela ramen först.

        Presenter skapas sist, efter att dess parent
        och buttonbar redan finns på plats.
        """

        # ======================================================
        # PRESENTATION FRAME
        # ======================================================

        self.presentation_frame = ctk.CTkFrame(
            self,
            width=self.presentation_frame_width,
            height=self.presentation_frame_height,
            fg_color="#10172A"
        )

        self.presentation_frame.pack(
            padx=5,
            pady=(5, 0)
        )

        self.presentation_frame.pack_propagate(
            False
        )

        # ======================================================
        # BUTTON BAR
        # ======================================================

        self.button_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        self.button_frame.pack(
            fill="x",
            padx=5,
            pady=(10, 5)
        )

        # ------------------------------------------------------
        # OPEN PLUGIN FOLDER
        # ------------------------------------------------------

        self.open_folder_button = ctk.CTkButton(
            self.button_frame,
            text=self._get_text(
                "duplicate_plugin_open_folder",
                "Open plugin folder"
            ),
            fg_color="#2E8B57",
            hover_color="#246B45",
            command=self._open_plugin_folder
        )

        self.open_folder_button.pack(
            side="left",
            expand=True,
            padx=(0, 5)
        )

        # ------------------------------------------------------
        # RESTART GAMEBRIDGE
        # ------------------------------------------------------

        self.restart_button = ctk.CTkButton(
            self.button_frame,
            text=self._get_text(
                "duplicate_plugin_restart",
                "Restart GameBridge"
            ),
            fg_color="#C00000",
            hover_color="#900000",
            command=self._restart_gamebridge
        )

        self.restart_button.pack(
            side="left",
            expand=True,
            padx=(5, 0)
        )

        # ======================================================
        # LAYOUT FIRST
        # ======================================================

        self.update_idletasks()

        # ======================================================
        # PRESENTATION
        #
        # Skapas EFTER att hela ramen och buttonbaren
        # redan har fått sin layout.
        # ======================================================

        self.presenter = PluginWarningPresenter(
            self.presentation_frame,
            localizer=self.localizer,
            width=self.presentation_width,
            height=self.presentation_height
        )

        self.presenter.place(
            x=self.presentation_border,
            y=self.presentation_border
        )

        self.update_idletasks()

    # ==========================================================
    # PLUGIN PATH
    # ==========================================================

    def _get_plugin_path(self):
        """
        Hämtar den registrerade plugin-sökvägen
        från RuntimeStateCore.
        """

        if self.runtime_state is None:
            return None

        return self.runtime_state.get_state(
            "duplicate_plugin_path",
            None
        )

    # ==========================================================
    # OPEN PLUGIN FOLDER
    # ==========================================================

    def _open_plugin_folder(self):
        """
        Öppnar den plugin-mapp som registrerats
        av AdapterLoader.
        """

        plugin_path = self._get_plugin_path()

        if not plugin_path:

            print(
                "[PLUGIN-WARNING] "
                "No duplicate plugin path available."
            )

            return

        if not os.path.isdir(plugin_path):

            print(
                "[PLUGIN-WARNING] "
                f"Plugin folder does not exist: {plugin_path}"
            )

            return

        try:

            if os.name == "nt":

                os.startfile(
                    plugin_path
                )

            elif os.name == "posix":

                subprocess.Popen(
                    [
                        "open"
                        if os.uname().sysname == "Darwin"
                        else "xdg-open",
                        plugin_path
                    ]
                )

        except Exception as e:

            print(
                "[PLUGIN-WARNING] "
                f"Failed to open plugin folder: {e}"
            )

    # ==========================================================
    # RESTART GAMEBRIDGE
    # ==========================================================

    def _restart_gamebridge(self):
        """
        Begär en kontrollerad soft reset av GameBridge.
        """

        if self.core_hub is None:

            print(
                "[PLUGIN-WARNING] "
                "No GameBridge Core available for soft reset."
            )

            return

        runtime_restart = getattr(
            self.core_hub,
            "runtime_restart",
            None
        )

        if runtime_restart is None:

            print(
                "[PLUGIN-WARNING] "
                "RuntimeRestartCore is not available."
            )

            return

        try:

            runtime_restart.restart_runtime()

            gui = getattr(
                self.core_hub,
                "gui",
                None
            )

            self.winfo_toplevel().destroy()

            if gui is not None:

                gui.after_idle(
                    gui._check_duplicate_plugin_warning
                )

        except Exception as e:

            print(
                "[PLUGIN-WARNING] "
                f"GameBridge soft reset failed: {e}"
            )