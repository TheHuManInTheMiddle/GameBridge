# -*- coding: utf-8 -*-

"""
GameBridge 16:9 Chat Presentation Component

KOPPLINGAR:
 - HÄMTAR FRÅN:
   - core/path_core.py
 - ANROPAS AV:
   - interface/client_gui.py
 - EXTERNA ANROP:
   - interface/gui_functions.py

ANSVAR:
 - Ren presentationsyta.
 - Statisk bakgrund.
 - Scrollbar textpresentation.
 - Channel 1 / Raw textpresentation.
 - Channel 2 telemetry-monitor.
 - Svart/vit text.
 - Normal/stor text.
 - Klickbara Channel 1-länkar.
 - Exponerar scroll-API till client_gui.

VIKTIGT:
 - Ingen AI-routing.
 - Ingen matrix-logik.
 - Ingen internetlogik.
 - Ingen core-routing.
 - client_gui äger flödet.
 - ChatWindow äger presentationen.

GEOMETRI:
 - client_gui äger ChatWindows externa storlek.
 - Basstorlek är 960 x 540.
 - ChatWindow ändrar aldrig root-fönstrets storlek.

LAGER:
 - Bakgrunden är statisk i HTML-dokumentet.
 - Textlagret ligger ovanpå bakgrunden.
 - HtmlFrame äger viewport och vertikal scrollning.
 - Horisontell scrollning är avstängd.
"""

import html
import os
import re

import customtkinter as ctk
from tkinterweb import HtmlFrame

from core.path_core import PathCore


class ChatWindow(ctk.CTkFrame):

    def __init__(
        self,
        master,
        localizer=None,
        handle_log_click_callback=None,
        **kwargs
    ):
        """
        Skapar ChatWindows rena presentationslager.
        """

        super().__init__(
            master,
            fg_color="transparent",
            **kwargs
        )

        self.localizer = localizer

        self.handle_log_click_callback = (
            handle_log_click_callback
        )

        self.bg_image_path = (
            PathCore.get_absolute_path(
                "assets",
                "background.png"
            )
        )

        self.is_large_text = False
        self.is_black_text = False

        self.messages_cache = []
        self.monitor_cache = []

        self.monitor_visible = False

        self._viewport_width = 960
        self._viewport_height = 540

        self._html_loaded = False

        self._build_components()

    # ==========================================================
    # COMPATIBILITY
    # ==========================================================

    @property
    def log_box(self):
        """
        Bakåtkompatibilitet.

        Äldre GUI-funktioner kan förvänta sig ett log_box-objekt.
        """

        return self

    # ==========================================================
    # VIEWPORT GEOMETRY
    # ==========================================================

    def _update_viewport_geometry(self, event=None):
        """
        Synkroniserar HtmlFrame med ChatWindows faktiska storlek.

        Ändrar aldrig root-fönstrets storlek.
        """

        try:

            self.update_idletasks()

            width = self.winfo_width()
            height = self.winfo_height()

            if width <= 1 or height <= 1:
                return

            self._viewport_width = max(
                960,
                width
            )

            self._viewport_height = max(
                540,
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
                "[CHAT-WINDOW-GEOMETRY] "
                f"Failed to synchronize viewport: {e}"
            )

    # ==========================================================
    # COMPONENT BUILD
    # ==========================================================

    def _build_components(self):
        """
        Skapar presentationsytan.

        HtmlFrame äger scrollningen.

        Ingen separat HTML-scrollcontainer används.
        """

        self.html_viewer = HtmlFrame(
            self,
            width=960,
            height=540,
            vertical_scrollbar="auto",
            horizontal_scrollbar=False,
            shrink=False,
            textwrap=True,
            on_link_click=self._handle_html_link
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
    # LINK HANDLING
    # ==========================================================

    def _handle_html_link(self, url):
        """
        Skickar en klickad URL vidare till GUI callback.

        ChatWindow öppnar aldrig länken själv.
        """

        if not url:
            return

        url = str(url)

        if not url.startswith(
            (
                "http://",
                "https://"
            )
        ):
            return

        if not self.handle_log_click_callback:
            return

        try:

            self.handle_log_click_callback(
                url
            )

        except TypeError:

            try:

                self.handle_log_click_callback(
                    self,
                    url
                )

            except Exception as e:

                print(
                    "[CHAT-WINDOW-LINK] "
                    f"Callback failed: {e}"
                )

        except Exception as e:

            print(
                "[CHAT-WINDOW-LINK] "
                f"Callback failed: {e}"
            )

    # ==========================================================
    # URL MARKUP
    # ==========================================================

    def _render_text_with_links(self, text):
        """
        Escape:ar vanlig text och gör http/https-URL:er
        till klickbara HTML-länkar.

        Ingen routing sker här.
        """

        raw_text = str(text)

        url_pattern = re.compile(
            r"(https?://[^\s<]+)"
        )

        parts = []
        cursor = 0

        for match in url_pattern.finditer(
            raw_text
        ):

            before = raw_text[
                cursor:match.start()
            ]

            url = match.group(1)

            trailing = ""

            while (
                url
                and url[-1] in ".,!?;:)"
            ):

                trailing = (
                    url[-1]
                    + trailing
                )

                url = url[:-1]

            if before:

                parts.append(
                    html.escape(
                        before
                    )
                )

            if url:

                safe_url = html.escape(
                    url,
                    quote=True
                )

                parts.append(
                    "<a "
                    f"href=\"{safe_url}\" "
                    "class=\"channel1-link\">"
                    f"{safe_url}"
                    "</a>"
                )

            if trailing:

                parts.append(
                    html.escape(
                        trailing
                    )
                )

            cursor = match.end()

        remainder = raw_text[
            cursor:
        ]

        if remainder:

            parts.append(
                html.escape(
                    remainder
                )
            )

        return "".join(parts)

    # ==========================================================
    # HTML
    # ==========================================================

    def _build_html_content(self):
        """
        Bygger hela presentationsdokumentet.

        Bakgrunden är statisk.

        Texten ligger ovanpå bakgrunden.

        Själva HtmlFrame sköter viewport och scrollning.
        """

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
        # TEXT SETTINGS
        # ------------------------------------------------------

        text_color = (
            "#000000"
            if self.is_black_text
            else "#FFFFFF"
        )

        font_size = (
            "18px"
            if self.is_large_text
            else "14px"
        )

        viewport_width = (
            self._viewport_width
        )

        viewport_height = (
            self._viewport_height
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

    overflow-x: hidden;

    box-sizing: border-box;
}}


*,
*::before,
*::after {{

    box-sizing: border-box;
}}


/* ==========================================================
   PRESENTATION DOCUMENT
   ========================================================== */

.presentation {{

    position: relative;

    width: {viewport_width}px;

    min-width: {viewport_width}px;

    min-height: {viewport_height}px;

    margin: 0;
    padding: 0;

    background-color: #10172A;
}}


/* ==========================================================
   STATIC BACKGROUND
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
   CHAT CONTENT
   ========================================================== */

.chat-content {{

    position: relative;

    z-index: 2;

    display: block;

    width: 100%;

    min-width: 0;

    min-height: {viewport_height}px;

    margin: 0;

    padding: 20px;

    background: transparent;
}}


/* ==========================================================
   MESSAGE
   ========================================================== */

.msg-line {{

    display: block;

    width: 100%;

    min-width: 0;

    margin: 0 0 5px 0;

    padding: 6px 10px;

    background: rgba(
        15,
        23,
        42,
        0.60
    );

    border-radius: 6px;

    color: {text_color};

    font-family: Consolas, monospace;

    font-size: {font_size};

    line-height: 1.35;

    word-wrap: break-word;

    overflow-wrap: anywhere;

    white-space: normal;
}}


/* ==========================================================
   LINKS
   ========================================================== */

.channel1-link {{

    color: inherit;

    text-decoration: underline;

    cursor: pointer;
}}


/* ==========================================================
   MONITOR
   ========================================================== */

.monitor-area {{

    width: 100%;

    min-width: 0;

    margin-top: 15px;

    padding: 10px;

    background: rgba(
        9,
        13,
        22,
        0.90
    );

    border: 1px solid #10B981;

    border-radius: 6px;

    color: #10B981;

    font-family: Consolas, monospace;

    font-size: 12px;

    line-height: 1.35;

    word-wrap: break-word;

    overflow-wrap: anywhere;

    white-space: normal;
}}

</style>

</head>

<body>

<div class="presentation">

    {img_element}

    <div
        class="chat-content"
        id="chat-content"
    >
"""

        # ======================================================
        # CHANNEL 1 / CHAT
        # ======================================================

        for sender, text in self.messages_cache:

            safe_sender = html.escape(
                str(sender)
            )

            rendered_text = (
                self._render_text_with_links(
                    text
                )
            )

            html_content += (
                "<div class='msg-line'>"
                f"<strong>[{safe_sender}]:</strong> "
                f"{rendered_text}"
                "</div>"
            )

        # ======================================================
        # CHANNEL 2 MONITOR
        # ======================================================

        if (
            self.monitor_visible
            and self.monitor_cache
        ):

            html_content += (
                "<div class='monitor-area'>"
                "<strong>"
                "■ KANAL 2 MONITOR:"
                "</strong>"
            )

            for log_line in self.monitor_cache:

                safe_log_line = html.escape(
                    str(log_line)
                )

                html_content += (
                    f"<br>{safe_log_line}"
                )

            html_content += (
                "</div>"
            )

        # ======================================================
        # CLOSE
        # ======================================================

        html_content += """

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

        Ingen routing.
        Ingen core-kommunikation.
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

            self.after_idle(
                self._scroll_to_bottom
            )

        except Exception as e:

            print(
                "[CHAT-WINDOW-HTML] "
                "Failed to refresh presentation layer: "
                f"{e}"
            )

    # ==========================================================
    # SCROLL API
    # ==========================================================

    def scroll_to(self, fraction):
        """
        Flyttar HtmlFrames vertikala viewport.

        0.0 = toppen
        1.0 = botten
        """

        try:

            fraction = max(
                0.0,
                min(
                    1.0,
                    float(fraction)
                )
            )

            self.html_viewer.yview_moveto(
                fraction
            )

            return True

        except Exception as e:

            print(
                "[CHAT-WINDOW-SCROLL] "
                f"Scroll command failed: {e}"
            )

            return False

    def scroll_to_top(self):
        """
        Flyttar presentationen till toppen.
        """

        return self.scroll_to(
            0.0
        )

    def scroll_to_bottom(self):
        """
        Flyttar presentationen till botten.
        """

        return self.scroll_to(
            1.0
        )

    def scroll_by(self, amount, units="units"):
        """
        Scrollar HtmlFrame relativt.

        Positivt värde = nedåt.
        Negativt värde = uppåt.
        """

        try:

            self.html_viewer.yview_scroll(
                int(amount),
                units
            )

            return True

        except Exception as e:

            print(
                "[CHAT-WINDOW-SCROLL] "
                f"Relative scroll failed: {e}"
            )

            return False

    def _scroll_to_bottom(self):
        """
        Intern wrapper efter rendering.
        """

        self.scroll_to_bottom()

    # ==========================================================
    # CHAT API
    # ==========================================================

    def append_chat_message(
        self,
        sender: str,
        text: str
    ):
        """
        Lägger till Channel 1-meddelande.

        client_gui äger flödet.
        ChatWindow renderar resultatet.
        """

        self.messages_cache.append(
            (
                sender,
                text
            )
        )

        self._refresh_presentation_layer()

    # ==========================================================
    # MONITOR API
    # ==========================================================

    def append_monitor_message(
        self,
        text: str
    ):
        """
        Lägger till Channel 2 telemetry-information.
        """

        self.monitor_cache.append(
            text
        )

        if self.monitor_visible:

            self._refresh_presentation_layer()

    # ==========================================================
    # TEXT SIZE
    # ==========================================================

    def set_text_dimensions(
        self,
        make_large: bool
    ):
        """
        Ändrar textstorlek.
        """

        self.is_large_text = make_large

        self._refresh_presentation_layer()

    # ==========================================================
    # TEXT COLOR
    # ==========================================================

    def set_text_mode_black(
        self,
        black_mode: bool
    ):
        """
        Ändrar textfärg mellan svart och vit.
        """

        self.is_black_text = black_mode

        self._refresh_presentation_layer()

    # ==========================================================
    # MONITOR VISIBILITY
    # ==========================================================

    def set_monitor_visibility(
        self,
        visible: bool
    ):
        """
        Visar eller döljer Channel 2-monitor.
        """

        self.monitor_visible = visible

        self._refresh_presentation_layer()