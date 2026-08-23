# -*- coding: utf-8 -*-
"""
GameBridge 16:9 HTML Chat Presentation Component
KOPPLINGAR:
 - HÄMTAR FRÅN:
   - core/path_core.py (för absolut sökväg till bakgrundsbild)
 - ANROPAS AV:
   - interface/client_gui.py
 - EXTERNA ANROP:
   - interface/gui_functions.py (via inskickade callbacks från client_gui)
"""
import customtkinter as ctk
from tkinterweb import HtmlFrame
import os
import re
from core.path_core import PathCore

class ChatWindow(ctk.CTkFrame):
    def __init__(self, master, localizer=None, handle_log_click_callback=None, **kwargs):
        """
        En presentationsvy i 16:9-format baserad på HTML/CSS som sköter 
        skalningen internt i webb-motorn för att undvika fönsterhopp.
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.localizer = localizer
        self.handle_log_click_callback = handle_log_click_callback
        
        self.bg_image_path = PathCore.get_absolute_path("interface", "background.png")
        
        # Interna tillstånd för textstil
        self.is_large_text = False
        self.is_black_text = False
        
        # Aktuell dynamisk zoomfaktor baserat på basmåttet 960 bredd
        self.current_scale_factor = 1.0
        
        # Datacache för att bygga om HTML-vyn dynamiskt
        self.messages_cache = []
        self.monitor_cache = []
        self.monitor_visible = False
        self._build_components()

    @property
    def log_box(self):
        """Property-länk för bakåtkompatibilitet med gui_functions."""
        return self

    def _build_components(self):
        """Skapar och förbereder HTML-presentationsytan."""
        # ANKARE 1 (Python): Webb-visaren fixeras i NW och fyller ut 16:9-ramen fullt ut
        self.html_viewer = HtmlFrame(self)
        self.html_viewer.place(relx=0.0, rely=0.0, anchor="nw", relwidth=1.0, relheight=1.0)
        
        if self.handle_log_click_callback:
            self.html_viewer.bind("<Button-1>", lambda event:
                self.handle_log_click_callback(self, event))
        
        # Bind egna storleksförändringar för att räkna ut den två-hörnsbaserade skalfaktorn
        self.bind("<Configure>", self._on_window_resized)
        self._refresh_presentation_layer()

    def _on_window_resized(self, event):
        """Räknar ut den exakta skalfaktorn i förhållande till basmåttet 960."""
        if event.width <= 1:
            return
        # Beräkna hur mycket större fönstret är än basmåttet 960
        new_scale = event.width / 960.0
        
        # Förhindra onödiga omladdningar om storleken knappt ändrats
        if abs(self.current_scale_factor - new_scale) > 0.01:
            self.current_scale_factor = new_scale
            self._refresh_presentation_layer()

    def _refresh_presentation_layer(self):
        """Genererar CSS och HTML där bilden spänns upp i 16:9 och texten scrollar."""
        img_element = ""
        if os.path.exists(self.bg_image_path):
            file_url = self.bg_image_path.replace("\\\\", "/").replace("\\", "/")
            # Skapar ett fysiskt bild-lager som tvingas skala stenhårt med dokumentets ramar
            img_element = f"<img class='bg-image-layer' src='file:///{file_url}' />"
        
        text_color = "#000000" if self.is_black_text else "#FFFFFF"
        font_size = "18px" if self.is_large_text else "14px"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        html, body {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            background-color: #1E293B;
            overflow: hidden;
            box-sizing: border-box;
        }}
        /* Bildlagret låses i NW och sträcks ut fysiskt till SW och SE i takt med fönsterskalningen */
        .bg-image-layer {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: fill; /* Tvingar bilden att följa de uppspända ankarmåtten slaviskt */
            z-index: 1;
        }}
        /* Chat-containern ligger ovanpå bilden och skalar linjärt från det fasta NW-ankaret */
        .chat-container {{
            position: absolute;
            top: 0;
            left: 0;
            width: 960px; /* Håller basupplösningen konstant internt */
            height: 540px;
            padding: 20px;
            box-sizing: border-box;
            overflow-y: auto;
            transform: scale({self.current_scale_factor});
            transform-origin: left top; /* Säkrar att all textuträkning utgår stenhårt från NW */
            z-index: 2;
        }}
        .msg-line {{
            padding: 6px 10px;
            margin-bottom: 5px;
            background: rgba(15, 23, 42, 0.6);
            border-radius: 6px;
            font-family: 'Consolas', monospace;
            color: {text_color};
            font-size: {font_size};
        }}
        .monitor-area {{
            margin-top: 15px;
            padding: 10px;
            background: rgba(9, 13, 22, 0.9);
            border: 1px solid #10B981;
            border-radius: 6px;
            color: #10B981;
            font-size: 12px;
            font-family: 'Consolas', monospace;
        }}
        </style>
        </head>
        <body>
        {img_element}
        <div class="chat-container">
        """
        
        for sender, text in self.messages_cache:
            html_content += f"<div class='msg-line'><strong>[{sender}]:</strong> {text}</div>"
        
        if self.monitor_visible and self.monitor_cache:
            html_content += "<div class='monitor-area'><strong>■ KANAL 2 MONITOR:</strong>"
            for log_line in self.monitor_cache:
                html_content += f"<br>{log_line}"
            html_content += "</div>"
        
        html_content += """
        </div>
        </body>
        </html>
        """
        self.html_viewer.load_html(html_content)

    def append_chat_message(self, sender: str, text: str):
        self.messages_cache.append((sender, text))
        self._refresh_presentation_layer()

    def append_monitor_message(self, text: str):
        self.monitor_cache.append(text)
        if self.monitor_visible:
            self._refresh_presentation_layer()

    def set_text_dimensions(self, make_large: bool):
        self.is_large_text = make_large
        self._refresh_presentation_layer()

    def set_text_mode_black(self, black_mode: bool):
        self.is_black_text = black_mode
        self._refresh_presentation_layer()

    def set_monitor_visibility(self, visible: bool):
        self.monitor_visible = visible
        self._refresh_presentation_layer()
