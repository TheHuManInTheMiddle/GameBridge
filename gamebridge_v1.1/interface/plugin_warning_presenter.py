# -*- coding: utf-8 -*-

"""
GameBridge Plugin Warning Presentation Component

KOPPLINGAR:
 - HÄMTAR FRÅN:
   - core/path_core.py
 - ANVÄNDS AV:
   - interface/plugin_warning_frame.py

ANSVAR:
 - Ren presentationsyta för plugin-varning.
 - 16:9 presentation med basstorlek 560 x 315.
 - Statisk bakgrund.
 - Lokaliserad varningstext.
 - Röd, fet 14px text.
 - HtmlFrame synkroniseras med faktisk frame-storlek.

VIKTIGT:
 - Ingen runtime-state-logik.
 - Ingen adapter-loader-logik.
 - Ingen Explorer-logik.
 - Ingen restart-logik.
 - Inga CTk-knappar.
 - Frame äger funktionella kontroller.
"""


import html
import os

import customtkinter as ctk
from tkinterweb import HtmlFrame

from core.path_core import PathCore


class PluginWarningPresenter(ctk.CTkFrame):

    def __init__(
        self,
        master,
        localizer=None,
        **kwargs
    ):
        """
        Skapar presentationsytan
        för plugin-varningen.
        """

        super().__init__(
            master,
            fg_color="transparent",
            **kwargs
        )

        self.localizer = localizer

        # ======================================================
        # VIEWPORT GEOMETRY
        # ======================================================

        self._viewport_width = 560
        self._viewport_height = 315

        # ======================================================
        # BACKGROUND
        # ======================================================

        self.bg_image_path = (
            PathCore.get_absolute_path(
                "assets",
                "plugin_warning.png"
            )
        )

        self._html_loaded = False

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
    # VIEWPORT GEOMETRY
    # ==========================================================

    def _update_viewport_geometry(
        self,
        event=None
    ):
        """
        Synkroniserar HtmlFrame med Warning-presenterns
        faktiska storlek.

        Ändrar aldrig root-fönstrets storlek.
        """

        try:

            self.update_idletasks()

            width = self.winfo_width()
            height = self.winfo_height()

            if width <= 1 or height <= 1:
                return

            self._viewport_width = max(
                560,
                width
            )

            self._viewport_height = max(
                315,
                height
            )

            if hasattr(
                self,
                "html_viewer"
            ):

                self.html_viewer.configure(
                    width=self._viewport_width,
                    height=self._viewport_height
                )

        except Exception as e:

            print(
                "[PLUGIN-WARNING-GEOMETRY] "
                f"Failed to synchronize viewport: {e}"
            )

    # ==========================================================
    # COMPONENT BUILD
    # ==========================================================

    def _build_components(self):
        """
        Skapar presentationsytan.

        HtmlFrame följer Warning-presenterns
        faktiska storlek.
        """

        self.html_viewer = HtmlFrame(
            self,
            width=560,
            height=315,
            vertical_scrollbar=False,
            horizontal_scrollbar=False,
            shrink=False,
            textwrap=True,
            on_link_click=None
        )

        self.html_viewer.place(
            x=0,
            y=0,
            relwidth=1.0,
            relheight=1.0
        )

        self.bind(
            "<Configure>",
            self._update_viewport_geometry
        )

        self._refresh_presentation_layer()

    # ==========================================================
    # HTML
    # ==========================================================

    def _build_html_content(self):
        """
        Bygger plugin-varningens rena
        presentationslager.
        """

        # ------------------------------------------------------
        # VIEWPORT
        # ------------------------------------------------------

        viewport_width = (
            self._viewport_width
        )

        viewport_height = (
            self._viewport_height
        )

        # ------------------------------------------------------
        # BACKGROUND
        # ------------------------------------------------------

        img_element = ""

        if os.path.exists(
            self.bg_image_path
        ):

            file_url = (
                self.bg_image_path
                .replace("\\", "/")
            )

            img_element = (
                "<img "
                "class='background-layer' "
                f"src='file:///{file_url}' "
                "alt='' "
                "/>"
            )

        # ------------------------------------------------------
        # LOCALIZED TEXT
        # ------------------------------------------------------

        title = self._get_text(
            "duplicate_plugin_title",
            "Duplicate plugin detected"
        )

        message = self._get_text(
            "duplicate_plugin_message",
            "Both an unpacked plugin and a .gbp package were found in the same plugin folder."
        )

        safe_title = html.escape(
            title
        )

        safe_message = html.escape(
            message
        )

        # ------------------------------------------------------
        # DOCUMENT
        # ------------------------------------------------------

        html_content = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<style>

html,
body {{

    margin: 0;
    padding: 0;

    width: {viewport_width}px;
    min-width: {viewport_width}px;

    min-height: {viewport_height}px;

    background-color: #10172A;

    overflow: hidden;

    box-sizing: border-box;
}}


*,
*::before,
*::after {{

    box-sizing: border-box;
}}


/* ==========================================================
   PRESENTATION
   ========================================================== */

.presentation {{

    position: relative;

    width: {viewport_width}px;

    min-width: {viewport_width}px;

    min-height: {viewport_height}px;

    margin: 0;
    padding: 0;

    background-color: #10172A;

    overflow: hidden;
}}


/* ==========================================================
   BACKGROUND
   ========================================================== */

.background-layer {{

    position: fixed;

    top: 0;
    left: 0;

    width: {viewport_width}px;
    height: {viewport_height}px;

    margin: 0;
    padding: 0;
    border: 0;

    object-fit: fill;

    z-index: 1;

    pointer-events: none;
}}


/* ==========================================================
   WARNING CONTENT
   ========================================================== */

.warning-content {{

    position: relative;

    z-index: 2;

    width: 100%;

    min-width: 0;

    min-height: {viewport_height}px;

    display: flex;

    flex-direction: column;

    justify-content: center;

    align-items: center;

    margin: 0;

    padding: 30px;

    background: transparent;
}}


/* ==========================================================
   WARNING TITLE
   ========================================================== */

.warning-title {{

    margin: 0 0 15px 0;

    color: #B91C1C;

    font-family: Arial, sans-serif;

    font-size: 16px;

    font-weight: bold;

    text-align: center;
}}


/* ==========================================================
   WARNING MESSAGE
   ========================================================== */

.warning-message {{

    width: 100%;

    max-width: 540px;

    margin: 0;

    color: #B91C1C;

    font-family: Arial, sans-serif;

    font-size: 16px;

    font-weight: bold;

    line-height: 1.4;

    text-align: center;

    word-wrap: break-word;

    overflow-wrap: anywhere;

    white-space: normal;
}}

</style>

</head>

<body>

<div class="presentation">

    {img_element}

    <div class="warning-content">

        <div class="warning-title">
            {safe_title}
        </div>

        <div class="warning-message">
            {safe_message}
        </div>

    </div>

</div>

</body>

</html>
"""

        return html_content

    # ==========================================================
    # REFRESH
    # ==========================================================

    def _refresh_presentation_layer(self):
        """
        Renderar om presentationslagret.

        Ingen runtime-routing.
        Ingen root-resize.
        """

        try:

            self._update_viewport_geometry()

            html_content = (
                self._build_html_content()
            )

            self.html_viewer.load_html(
                html_content
            )

            self._html_loaded = True

        except Exception as e:

            print(
                "[PLUGIN-WARNING-HTML] "
                "Failed to refresh presentation layer: "
                f"{e}"
            )