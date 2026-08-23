# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
- HÄMTAR FRÅN: interface/ui_event_queue.py, core/telemetry_core.py, 
core/model_monitor_core.py, interface/gui_functions.py, interface/chat_window.py,
core/path_core.py
- ANROPAS AV: main/main.py
"""
import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import threading
import re
import os
import sys

from core.path_core import PathCore
from interface.ui_event_queue import UIEventQueue
from core.telemetry_core import TelemetryCore
from core.model_monitor_core import ModelMonitorCore
from interface.chat_window import ChatWindow
from interface.gui_functions import (
    function_on_ai_toggle, function_on_internet_toggle, function_sync_matrix_to_core,
    function_on_telemetry_toggle, function_on_lock_toggle, function_on_model_change, 
    function_on_adapter_change, function_trigger_text_input, function_handle_log_double_click
)

class GameBridgeGUI(ctk.CTk):
    def __init__(self, core_hub=None, matrix=None, localizer=None):
        super().__init__()
        
        # FIXED: Beroenden injiceras omedelbart i konstruktorn för att säkra språksynken vid boot
        self.core_hub = core_hub
        self.matrix = matrix 
        self.localizer = localizer 
        self.version = "3.5.0"
        
        self.event_queue = UIEventQueue()
        self.model_monitor = ModelMonitorCore()
        
        # Fönstret startar som överst, men kan muteras dynamiskt av användaren
        self.attributes("-topmost", True)
        
        # UTRENSAD: Ingen hårdkodad geometry eller 960x540-låsning på fönsternivå längre! 🔓
        
        self._build_ui()
        self._process_gui_queue_loop()
    def on_ai_toggle(self):
        function_on_ai_toggle(self)

    def on_internet_toggle(self):
        function_on_internet_toggle(self)

    def on_topmost_toggle(self):
        """Dynamically flips the OS window layering priority based on user check state."""
        if hasattr(self, 'topmost_toggle_switch'):
            is_on = self.topmost_toggle_switch.get() == 1
            self.attributes("-topmost", is_on)
            state_msg = "Always-on-Top activated." if is_on else "Always-on-Top deactivated. Background persistence active."
            self.append_log("SYSTEM", state_msg)

    def sync_matrix_to_core(self):
        function_sync_matrix_to_core(self)

    def on_telemetry_toggle(self):
        function_on_telemetry_toggle(self)

    def on_lock_toggle(self):
        # FIXED: Slussas nu transaktionellt ut till gui_functions för att mutera HardwareIO
        function_on_lock_toggle(self)
        if hasattr(self, 'lock_icon_label') and hasattr(self, 'lock_switch'):
            icon = "⌨️🔒" if self.lock_switch.get() == 1 else "⌨️🔓"
            self.lock_icon_label.configure(text=icon)

    def on_voice_mode_change(self, mode):
        pass

    def _safe_update_lamp_color(self, color_hex: str):
        self.event_queue.dispatch(lambda: self.ai_status_lamp.configure(text_color=color_hex))

    def start_hotkey_capture(self):
        if self.core_hub:
            self.hotkey_btn.configure(text="  ⌨️⏳", fg_color="#DC2626")
            threading.Thread(target=self.core_hub.capture_new_hotkey, daemon=True).start()

    def on_model_change(self, selected_model):
        function_on_model_change(self, selected_model)
        
    # BACKÅTKOMPATIBILITET FÖR GUI_FUNCTIONS
    @property
    def log_box(self):
        return self.chat_window.log_box
        
    @property
    def entry_field(self):
        return self.entry_field_widget

    def append_log(self, sender: str, text: str):
        """Slussar vidare meddelandet trådsäkert till det nya externa chatfönstret."""
        self.chat_window.append_chat_message(sender, text)

    def _process_gui_queue_loop(self):
        self.event_queue.process_next_batch()
        self.after(50, self._process_gui_queue_loop)
    def on_adapter_change(self, selected_adapter):
        """Växlar adapter och uppdaterar den kombinerade Connect/Disconnect-knappens utseende."""
        function_on_adapter_change(self, selected_adapter)
        
        no_adapter_text = self.localizer.get_text("no_adapter") if self.localizer else "No Adapter Loaded"
        
        if selected_adapter == no_adapter_text:
            boot_str = self.localizer.get_text("boot_btn") if self.localizer else "Launch / Attach App"
            self.boot_target_btn.configure(text=boot_str, fg_color="#059669", hover_color="#10B981", state="disabled")
        else:
            boot_str = self.localizer.get_text("boot_btn") if self.localizer else "Launch / Attach App"
            self.boot_target_btn.configure(text=boot_str, fg_color="#059669", hover_color="#10B981", state="normal")

    def trigger_combined_adapter_action(self):
        """Hanterar både Connect och Disconnect i en och samma knapp baserat på dess nuvarande tillstånd."""
        no_adapter_text = self.localizer.get_text("no_adapter") if self.localizer else "No Adapter Loaded"
        disconnect_str = self.localizer.get_text("disconnect_btn") if self.localizer else "Disconnect"
        
        if self.boot_target_btn.cget("text") == disconnect_str:
            self.adapter_selector.set(no_adapter_text)
            self.on_adapter_change(no_adapter_text)
        else:
            if self.core_hub:
                self.append_log("SYSTEM", "Initializing manual boot sequence...")
                self.core_hub.boot_target_application()
            
            self.boot_target_btn.configure(text=disconnect_str, fg_color="#DC2626", hover_color="#EF4444")

    def trigger_text_input(self):
        function_trigger_text_input(self)

    # REGLAGEMETODER SOM PRATAR MED DET EXTERNA CHATTFÖNSTRET
    def on_text_size_toggle(self):
        is_large = self.text_size_switch.get() == 1
        self.chat_window.set_text_dimensions(is_large)

    def on_text_color_toggle(self):
        is_black = self.text_color_switch.get() == 1
        self.chat_window.set_text_mode_black(is_black)

    def toggle_monitor_panel(self):
        is_visible = self.monitor_switch.get() == 1
        self.chat_window.set_monitor_visibility(is_visible)
    def _build_ui(self):
        """Renders standard application layout widgets using current localization strings with strict fallbacks."""
        title_str = self.localizer.get_text("title") if self.localizer else "G.A.M.E. B.R.I.D.G.E."
        self.title(title_str)
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        
        # 1. TOP PANEL FRAME AND CORE WIDGETS
        self.top_frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        self.top_frame.pack(pady=(10, 5), padx=10, fill="x")
        self.ai_status_lamp = ctk.CTkLabel(self.top_frame, text="●", text_color="#9CA3AF", font=("Arial", 22))
        self.ai_status_lamp.pack(side="left", padx=(15, 5), pady=10)
        status_str = self.localizer.get_text("status_ready") if self.localizer else "Status: Ready"
        self.status_label = ctk.CTkLabel(self.top_frame, text=status_str, font=("Arial", 13, "bold"))
        self.status_label.pack(side="left", padx=5, pady=10)
        
        ai_toggle_str = self.localizer.get_text("ai_toggle") if self.localizer else "AI Active"
        self.ai_toggle_switch = ctk.CTkSwitch(self.top_frame, text=ai_toggle_str, command=self.on_ai_toggle, font=("Arial", 12, "bold"))
        self.ai_toggle_switch.pack(side="left", padx=10, pady=10)
        self.ai_toggle_switch.deselect()
        
        internet_toggle_str = self.localizer.get_text("internet_toggle") if self.localizer else "Internet AI"
        self.internet_toggle = ctk.CTkSwitch(self.top_frame, text=internet_toggle_str, command=self.on_internet_toggle, font=("Arial", 12, "bold"), progress_color="#10B981")
        self.internet_toggle.pack(side="left", padx=10, pady=10)
        self.internet_toggle.deselect()
        
        boot_str = self.localizer.get_text("boot_btn") if self.localizer else "Launch / Attach App"
        self.boot_target_btn = ctk.CTkButton(self.top_frame, text=boot_str, command=self.trigger_combined_adapter_action, width=150, fg_color="#059669", hover_color="#10B981", state="disabled")
        self.boot_target_btn.pack(side="right", padx=(15, 15), pady=10)
        
        no_adapter_text = self.localizer.get_text("no_adapter") if self.localizer else "No Adapter Loaded"
        initial_adapters = [no_adapter_text]
        if self.core_hub and hasattr(self.core_hub, 'available_adapters'):
            discovered = list(self.core_hub.available_adapters.keys())
            if discovered:
                initial_adapters.extend(discovered)
        self.adapter_selector = ctk.CTkOptionMenu(self.top_frame, values=initial_adapters, command=self.on_adapter_change)
        self.adapter_selector.pack(side="right", padx=10, pady=10)
        self.adapter_selector.set(no_adapter_text)
        self.model_selector = ctk.CTkOptionMenu(self.top_frame, values=self.model_monitor.fetch_installed_models(), command=self.on_model_change)
        self.model_selector.pack(side="right", padx=10, pady=10)
        if self.core_hub and hasattr(self.core_hub, 'global_config'):
            saved_model = self.core_hub.global_config.get("ai_model_name", "sailwind-pilot")
            if saved_model in self.model_selector.cget("values"):
                self.model_selector.set(saved_model)
        
        # 2. SIGNAL INSTRUMENT MATRIX FRAME
        self.matrix_frame = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color="#1E293B")
        self.matrix_frame.pack(pady=5, padx=10, fill="x")
        matrix_title_str = self.localizer.get_text("matrix_title") if self.localizer else "CHANNEL CONTROL"
        self.matrix_title = ctk.CTkLabel(self.matrix_frame, text=matrix_title_str, font=("Arial", 11, "bold"), text_color="#94A3B8")
        self.matrix_title.pack(anchor="w", padx=15, pady=(8, 2))
        self.controls_grid = ctk.CTkFrame(self.matrix_frame, fg_color="transparent")
        self.controls_grid.pack(fill="x", padx=15, pady=(0, 10))
        
        # 3. POPULATE THE CONTROLS GRID
        chat_switch_str = (
            self.localizer.get_text("chat_switch")
            if self.localizer
            else "Text Chat"
        )
        self.chat_switch = ctk.CTkSwitch(
            self.controls_grid,
            text=chat_switch_str,
            command=self.sync_matrix_to_core,
            font=("Arial", 12),
            text_color="#E2E8F0",
        )
        self.chat_switch.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.chat_switch.deselect()
        
        voice_label_str = (
            self.localizer.get_text("voice_label")
            if self.localizer
            else "Voice Mode:"
        )
        self.voice_label = ctk.CTkLabel(
            self.controls_grid,
            text=voice_label_str,
            font=("Arial", 12),
            text_color="#E2E8F0",
        )
        self.voice_label.grid(
            row=0, column=1, padx=(20, 5), pady=10, sticky="w"
        )

        # Originalikoner där Av och Lyssna görs 2 pixlar större i relation till mittenikonen
        voice_modes_list = ["  🔇 ", "🔘🎙️", "  🎙️ "]
        voice_mode_values = ["OFF", "PTT", "LISTEN"]

        self.voice_mode_btn = ctk.CTkSegmentedButton(
            self.controls_grid,
            values=voice_modes_list,
            command=lambda mode: self.on_voice_mode_change(
                voice_mode_values[voice_modes_list.index(mode)]
            ),
            font=("Arial", 14),
            selected_color="#3B82F6",  # Standard blå dropdown-färg som bas
        )
        self.voice_mode_btn.grid(row=0, column=2, padx=5, pady=10, sticky="w")
        self.voice_mode_btn.set(voice_modes_list[0])
        
        # Dynamisk färg- och storlekskodning (Röd för Av, Grön för PTT/Listen)
        def _update_voice_btn_color(mode):
            if mode == "  🔇 ":
                self.voice_mode_btn.configure(selected_color="#DC2626", font=("Arial", 16)) # 2px större för 🔇
            elif mode == "🔘🎙️":
                self.voice_mode_btn.configure(selected_color="#059669", font=("Arial", 14)) # Standard för mitten
            elif mode == "  🎙️ ":
                self.voice_mode_btn.configure(selected_color="#059669", font=("Arial", 16)) # 2px större för 🎙️
        
        # Hooka färg/storleksändringen utan att röra GameBridge-logiken
        orig_voice_change = self.on_voice_mode_change
        def _wrapped_voice_change(mode):
            _update_voice_btn_color(mode)
            orig_voice_change(mode)
        self.voice_mode_btn.configure(command=_wrapped_voice_change)
        _update_voice_btn_color(voice_modes_list[0])
        
        tel_switch_str = self.localizer.get_text("telemetry_switch") if self.localizer else "Read Telemetry"
        self.read_telemetry_switch = ctk.CTkSwitch(self.controls_grid, text=tel_switch_str, command=self.on_telemetry_toggle, font=("Arial", 12), text_color="#E2E8F0")
        self.read_telemetry_switch.grid(row=0, column=3, padx=40, pady=10, sticky="w")
        self.read_telemetry_switch.deselect()
        write_switch_str = self.localizer.get_text("write_switch") if self.localizer else "Write to Adapter"
        self.write_adapter_switch = ctk.CTkSwitch(self.controls_grid, text=write_switch_str, command=self.sync_matrix_to_core, font=("Arial", 12), text_color="#E2E8F0")
        self.write_adapter_switch.grid(row=0, column=4, padx=20, pady=10, sticky="w")
        self.write_adapter_switch.deselect()

        # 5. LOWER FRAME INTERACTIVE INPUT CONTROLS
        self.control_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.control_frame.pack(pady=(0, 5), padx=10, fill="x", side="bottom")
        
        # Låsikon uppdaterad till originaletikett med 2px större tangentbordsikon till vänster
        self.lock_icon_label = ctk.CTkLabel(self.control_frame, text="⌨️🔓", font=("Arial", 16))
        self.lock_icon_label.pack(side="left", padx=(5, 2))
        
        self.lock_switch = ctk.CTkSwitch(self.control_frame, text="", command=self.on_lock_toggle, width=45)
        self.lock_switch.pack(side="left", padx=(0, 15))
        self.lock_switch.deselect()
        
        # Säkerställ att ikonen ändras till stängd vid toggle utan att bryta GameBridge-logiken högre upp
        orig_lock_toggle = self.on_lock_toggle
        def _wrapped_lock_toggle():
            orig_lock_toggle()
            # Överskriver texten direkt här nere för att matcha din nya ikondesign och storlek
            icon = "⌨️🔒" if self.lock_switch.get() == 1 else "⌨️🔓"
            self.lock_icon_label.configure(text=icon)
        self.lock_switch.configure(command=_wrapped_lock_toggle)
        
        topmost_str = self.localizer.get_text("topmost_toggle") if self.localizer else "Stay on Top"
        self.topmost_toggle_switch = ctk.CTkSwitch(self.control_frame, text=topmost_str, command=self.on_topmost_toggle, font=("Arial", 12), progress_color="#3B82F6")
        self.topmost_toggle_switch.pack(side="left", padx=10)
        self.topmost_toggle_switch.select()
        
        self.text_size_switch = ctk.CTkSwitch(self.control_frame, text="🔍 Stor text", command=self.on_text_size_toggle)
        self.text_size_switch.pack(side="left", padx=10)
        
        self.text_color_switch = ctk.CTkSwitch(self.control_frame, text="● Svart text", command=self.on_text_color_toggle)
        self.text_color_switch.pack(side="left", padx=10)
        self.text_color_switch.deselect()
        
        self.monitor_switch = ctk.CTkSwitch(self.control_frame, text="● K2 Mon", command=self.toggle_monitor_panel)
        self.monitor_switch.pack(side="left", padx=10)
        
        # Hotkey-knapp utan plus ( 🔘🎙️) och med 2px större storlek (font 16)
        self.hotkey_btn = ctk.CTkButton(
            self.control_frame, 
            text="  🔘🎙️", 
            command=self.start_hotkey_capture, 
            width=65, 
            font=("Arial", 16, "bold"), 
            fg_color="#374151", 
            hover_color="#4B5563"
        )
        self.hotkey_btn.pack(side="right", padx=5)
        # INTERAKTIV INMATNINGSRAD (Ligger fast i botten, under allt annat)
        self.bottom_input_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.bottom_input_frame.pack(pady=10, padx=10, fill="x", side="bottom")
        
        placeholder_str = self.localizer.get_text("input_placeholder") if self.localizer else "Type message..."
        self.entry_field_widget = ctk.CTkEntry(self.bottom_input_frame, placeholder_text=placeholder_str, font=("Arial", 12))
        self.entry_field_widget.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_field_widget.bind("<Return>", lambda event: self.trigger_text_input())
        
        send_str = self.localizer.get_text("send_btn") if self.localizer else "Send"
        self.send_button = ctk.CTkButton(self.bottom_input_frame, text=send_str, command=self.trigger_text_input, width=100)
        self.send_button.pack(side="right")
        
        # 4. MONTERING AV EXTERN CHATTKOMPONENT (CHATWINDOW PRESENTATION)
        # Justerar de övriga panelerna så att de förankras strikt mot fönstret
        self.top_frame.pack_configure(side="top", fill="x", expand=False)
        self.matrix_frame.pack_configure(side="top", fill="x", expand=False)
        self.bottom_input_frame.pack_configure(side="bottom", fill="x", expand=False)
        self.control_frame.pack_configure(side="bottom", fill="x", expand=False)

        # Skapar mittensektionen som tar upp allt resterande utrymme i fönstret
        self.chat_anchor_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.chat_anchor_container.pack(pady=5, padx=10, fill="both", expand=True)

        # Det fasta 16:9-ankaret (låst till NW) fungerar nu som den fasta yttre ramen
        self.chat_anchor_surface = ctk.CTkFrame(self.chat_anchor_container, fg_color="#10172A")
        self.chat_anchor_surface.place(relx=0.0, rely=0.0, anchor="nw")

        # Laddar in det riktiga presentationslagret (ChatWindow) direkt i vårt 16:9-ankare
        self.chat_window = ChatWindow(
            master=self.chat_anchor_surface,
            localizer=self.localizer,
            handle_log_click_callback=function_handle_log_double_click
        )
        # Låter presentationen, bakgrundsbilden och texterna fylla ut hela ankarytan
        self.chat_window.pack(fill="both", expand=True)

        def _enforce_16_9_aspect(event=None):
            # Tvinga fönsterhanteraren att beräkna de exakta måtten för övriga paneler
            self.update_idletasks()
            
            # Räkna ut exakt hur mycket plats de andra GUI-elementen stjäl från skärmen
            overhead_w = self.winfo_width() - self.chat_anchor_container.winfo_width()
            overhead_h = self.winfo_height() - self.chat_anchor_container.winfo_height()
            
            # Sätt programmets absoluta minimistorlek: Chattrutan (960x540) + övriga panelers pixlar
            min_window_w = 960 + max(0, overhead_w)
            min_window_h = 540 + max(0, overhead_h)
            self.minsize(min_window_w, min_window_h)

            # Hämta nuvarande tillgängliga utrymme för beräkning av 16:9-skalning uppåt
            container_w = self.chat_anchor_container.winfo_width()
            container_h = self.chat_anchor_container.winfo_height()
            
            if container_w <= 1 or container_h <= 1:
                return
                
            # Beräkna 16:9-mått utifrån tillgängligt utrymme med strikt flyttalsmatematik
            if container_w / container_h > 16.0 / 9.0:
                target_h = container_h
                target_w = int(container_h * (16.0 / 9.0))
            else:
                target_w = container_w
                target_h = int(container_w * (9.0 / 16.0))
                
            # Om uträkningen faller under basmåttet på grund av fönstertröghet, tvinga golvet
            if target_w < 960 or target_h < 540:
                target_w = 960
                target_h = 540
                
            # Låser ramens dimensioner stenhårt till 16:9 i övre vänstra hörnet utan fördröjning
            self.chat_anchor_surface.place_configure(width=target_w, height=target_h)

        # Bind storleksförändringar och kör en direkt rendering vid uppstart
        self.chat_anchor_container.bind("<Configure>", _enforce_16_9_aspect)
        self.update_idletasks()
        _enforce_16_9_aspect()
        
        self.model_monitor.start_lamp_monitor(
            core_hub_callback=lambda: self.core_hub,
            update_lamp_ui_callback=self._safe_update_lamp_color,
            get_switch_state_callback=lambda: self.ai_toggle_switch.get()
        )

