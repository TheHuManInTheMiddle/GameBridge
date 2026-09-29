# -*- coding: utf-8 -*-

"""
GameBridge 16:9 Chat Presentation Component

CONNECTIONS:
 - FETCHES FROM:
   - core/path_core.py
 - CALLED BY:
   - interface/client_gui.py
 - EXTERNAL CALLS:
   - interface/gui_functions.py

RESPONSIBILITIES:
 - Pure presentation layer.
 - Static background.
 - Scrollable text presentation.
 - Channel 1 / raw text presentation.
 - Channel 2 telemetry monitor.
 - Configurable text color.
 - Normal/large text.
 - Clickable Channel 1 links.
 - Exposes scroll API to client_gui.

IMPORTANT:
 - No AI routing.
 - No matrix logic.
 - No internet logic.
 - No core routing.
 - client_gui owns the flow.
 - ChatWindow owns presentation.

GEOMETRY:
 - client_gui owns ChatWindow's external size.
 - Base size is 960 x 540.
 - ChatWindow never changes the root window size.

LAYERS:
 - Background is static in the HTML document.
 - Text layer is rendered above the background.
 - HtmlFrame owns the viewport and vertical scrolling.
 - Horizontal scrolling is disabled.
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
        Creates ChatWindow's pure presentation layer.
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

        # Current chat text color.
        # The default matches ConfigCore's persistent default.
        self.text_color = "#FFFFFF"

        self.messages_cache = []
        self.monitor_cache = []

        self.channel2_monitor_visible = False
        self.telemetry_monitor_visible = False

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
        Provides backwards compatibility.

        Older GUI functions may expect a log_box object.
        """

        return self

    # ==========================================================
    # VIEWPORT GEOMETRY
    # ==========================================================

    def _update_viewport_geometry(self, event=None):
        """
        Synchronizes HtmlFrame with ChatWindow's actual size.

        Never changes the root window size.
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
                "Failed to synchronize viewport: "
                f"{e}"
            )

    # ==========================================================
    # COMPONENT BUILD
    # ==========================================================

    def _build_components(self):
        """
        Creates the presentation surface.

        HtmlFrame owns scrolling.

        No separate HTML scroll container is used.

        The visual scrollbar control is managed by client_gui.
        """

        self.html_viewer = HtmlFrame(
            self,
            width=960,
            height=540,
            vertical_scrollbar=False,
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
        Sends a clicked URL to the GUI callback.

        ChatWindow never opens the link itself.
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
        Escapes regular text and converts HTTP/HTTPS URLs
        into clickable HTML links.

        No routing is performed here.
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
        Builds the complete presentation document.

        The background is static.

        Text is rendered above the background.

        HtmlFrame handles the viewport and scrolling.
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

        text_color = self.text_color

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

    padding: 0;

    background: transparent;
}}


/* ==========================================================
   MESSAGE
   ========================================================== */

.msg-line {{

    display: block;

    width: 95%;

    min-width: 0;

    margin: 5px auto;

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


.msg-line:first-child {{

    margin-top: 20px;
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
            self.channel2_monitor_visible
            and self.monitor_cache
        ):

            html_content += (
                "<div class='monitor-area'>"
                "<strong>"
                "■ CHANNEL 2:"
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
        # TELEMETRY MONITOR
        # ======================================================

        if (
            self.telemetry_monitor_visible
            and self.monitor_cache
        ):

            html_content += (
                "<div class='monitor-area'>"
                "<strong>"
                "■ TELEMETRY:"
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
        Re-renders the presentation layer.

        No routing.
        No core communication.
        No root resizing.
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

            self.after(
                50,
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
        Moves HtmlFrame's vertical viewport.

        0.0 = top
        1.0 = bottom
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
        Moves the presentation to the top.
        """

        return self.scroll_to(
            0.0
        )

    def scroll_to_bottom(self):
        """
        Moves the presentation to the bottom.
        """

        return self.scroll_to(
            1.0
        )

    def scroll_by(self, amount, units="units"):
        """
        Scrolls HtmlFrame relatively.

        Positive value = downward.
        Negative value = upward.
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
        Internal wrapper used after rendering.
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
        Adds a Channel 1 message.

        client_gui owns the flow.
        ChatWindow renders the result.
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
        Adds monitor information.
        """

        self.monitor_cache.append(
            text
        )

        if (
            self.channel2_monitor_visible
            or self.telemetry_monitor_visible
        ):

            self._refresh_presentation_layer()

    # ==========================================================
    # TEXT SIZE
    # ==========================================================

    def set_text_dimensions(
        self,
        make_large: bool
    ):
        """
        Changes text size.
        """

        self.is_large_text = make_large

        self._refresh_presentation_layer()

    # ==========================================================
    # TEXT COLOR
    # ==========================================================

    def set_text_color(
        self,
        color: str
    ):
        """
        Sets the current chat text color and refreshes
        the presentation layer immediately.
        """

        if not color:
            return

        self.text_color = str(
            color
        ).strip()

        self._refresh_presentation_layer()

    def set_text_mode_black(
        self,
        black_mode: bool
    ):
        """
        Compatibility wrapper for the previous black/white
        text-color control.

        New code should use set_text_color().
        """

        self.set_text_color(
            "#000000"
            if black_mode
            else "#FFFFFF"
        )

    # ==========================================================
    # MONITOR VISIBILITY
    # ==========================================================

    def set_channel2_monitor_visibility(
        self,
        visible: bool
    ):
        """
        Shows or hides the Channel 2 monitor.
        """

        self.channel2_monitor_visible = bool(
            visible
        )

        self._refresh_presentation_layer()

    def set_telemetry_monitor_visibility(
        self,
        visible: bool
    ):
        """
        Shows or hides the Telemetry monitor.
        """

        self.telemetry_monitor_visible = bool(
            visible
        )

        self._refresh_presentation_layer()

    def set_monitor_visibility(
        self,
        visible: bool
    ):
        """
        Compatibility wrapper for the previous monitor control.

        The legacy monitor switch controls both presentation
        monitors together.
        """

        visible = bool(
            visible
        )

        self.channel2_monitor_visible = visible
        self.telemetry_monitor_visible = visible

        self._refresh_presentation_layer()