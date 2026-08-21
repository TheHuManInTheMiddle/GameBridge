# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
- HÄMTAR FRÅN: interface/ui_event_queue.py, core/telemetry_core.py, 
core/model_monitor_core.py, interface/gui_functions.py
- ANROPAS AV: main/main.py
"""
import customtkinter as ctk
import threading
import re
from interface.ui_event_queue import UIEventQueue
from core.telemetry_core import TelemetryCore
from core.model_monitor_core import ModelMonitorCore
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

    def on_voice_mode_change(self, mode):
        self.append_log("HARDWARE", f"Voice mode modified to: [{mode}]")

    def _safe_update_lamp_color(self, color_hex: str):
        self.event_queue.dispatch(lambda: self.ai_status_lamp.configure(text_color=color_hex))

    def start_hotkey_capture(self):
        if self.core_hub:
            wait_str = self.localizer.get_text("hotkey_wait") if self.localizer else "Wait..."
            self.hotkey_btn.configure(text=wait_str, fg_color="#DC2626")
            threading.Thread(target=self.core_hub.capture_new_hotkey, daemon=True).start()

    def on_model_change(self, selected_model):
        function_on_model_change(self, selected_model)

    def append_log(self, sender: str, text: str):
        """Routes human or AI text messages safely to the conversation log view and highlights links."""
        def _execute():
            self.log_box.configure(state="normal")
            
            # Räkna ut var den nya raden kommer att börja
            start_index = self.log_box.index("end-1c")
            
            # Bygg upp hela textraden
            full_text = f"\n[{sender}]: {text}\n"
            self.log_box.insert("end", full_text)
            
            # Hitta länk-positioner inuti den nyss tillagda texten via Regex
            for match in re.finditer(r'(https?://[^\s\)\}\]\",\']+)', full_text):
                link_start = match.start()
                link_end = match.end()
                
                # Omvandla till Tkinter-koordinater baserat på radens startpunkt
                tk_start = f"{start_index} + {link_start} chars"
                tk_end = f"{start_index} + {link_end} chars"
                
                # Applicera hyperlink-taggen över länken
                self.log_box.tag_add("hyperlink", tk_start, tk_end)
                
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
            self.update_idletasks()
            
        self.event_queue.dispatch(_execute)

    def _process_gui_queue_loop(self):
        self.event_queue.process_next_batch()
        self.after(50, self._process_gui_queue_loop)

    def on_adapter_change(self, selected_adapter):
        """Växlar adapter och uppdaterar den kombinerade Connect/Disconnect-knappens utseende."""
        function_on_adapter_change(self, selected_adapter)
        
        no_adapter_text = self.localizer.get_text("no_adapter") if self.localizer else "No Adapter Loaded"
        
        if selected_adapter == no_adapter_text:
            # Revertera knappen till standard "Boot/Attach" i avstängt läge
            boot_str = self.localizer.get_text("boot_btn") if self.localizer else "Launch / Attach App"
            self.boot_target_btn.configure(text=boot_str, fg_color="#059669", hover_color="#10B981", state="disabled")
        else:
            # Gör knappen grön och redo för anslutning
            boot_str = self.localizer.get_text("boot_btn") if self.localizer else "Launch / Attach App"
            self.boot_target_btn.configure(text=boot_str, fg_color="#059669", hover_color="#10B981", state="normal")

    def trigger_combined_adapter_action(self):
        """Hanterar både Connect och Disconnect i en och samma knapp baserat på dess nuvarande tillstånd."""
        no_adapter_text = self.localizer.get_text("no_adapter") if self.localizer else "No Adapter Loaded"
        disconnect_str = self.localizer.get_text("disconnect_btn") if self.localizer else "Disconnect"
        
        # Om knappen visar "Disconnect", fungerar den som en urkoppling
        if self.boot_target_btn.cget("text") == disconnect_str:
            self.adapter_selector.set(no_adapter_text)
            self.on_adapter_change(no_adapter_text)
        else:
            # Annars körs den vanliga uppstarts- och anslutningssekvensen
            if self.core_hub:
                self.append_log("SYSTEM", "Initializing manual boot sequence...")
                self.core_hub.boot_target_application()
                
                # Förvandla direkt knappen till en röd "Disconnect"-knapp efter lyckat anrop
                self.boot_target_btn.configure(text=disconnect_str, fg_color="#DC2626", hover_color="#EF4444")

    def trigger_text_input(self):
        function_trigger_text_input(self)

    def _build_ui(self):
        """Renders standard application layout widgets using current localization strings with strict fallbacks."""
        title_str = self.localizer.get_text("title") if self.localizer else "G.A.M.E. B.R.I.D.G.E."
        self.title(title_str)

        # 1. TOP PANEL FRAME AND CORE WIDGETS
        self.top_frame = ctk.CTkFrame(self, corner_radius=10)
        self.top_frame.pack(pady=(10, 5), padx=10, fill="x")

        self.ai_status_lamp = ctk.CTkLabel(self.top_frame, text="●", text_color="#9CA3AF", font=("Arial", 22))
        self.ai_status_lamp.pack(side="left", padx=(15, 5), pady=10)

        status_str = self.localizer.get_text("status_ready") if self.localizer else "Status: Ready"
        self.status_label = ctk.CTkLabel(self.top_frame, text=status_str, font=("Arial", 13, "bold"))
        self.status_label.pack(side="left", padx=5, pady=10)

        # Central Engine Activation Switch
        ai_toggle_str = self.localizer.get_text("ai_toggle") if self.localizer else "AI Active"
        self.ai_toggle_switch = ctk.CTkSwitch(self.top_frame, text=ai_toggle_str, command=self.on_ai_toggle, font=("Arial", 12, "bold"))
        self.ai_toggle_switch.pack(side="left", padx=10, pady=10)
        self.ai_toggle_switch.deselect()

        # Internet AI capability toggle (Dras via LocalizationCore)
        internet_toggle_str = self.localizer.get_text("internet_toggle") if self.localizer else "Internet AI"
        self.internet_toggle = ctk.CTkSwitch(self.top_frame, text=internet_toggle_str, command=self.on_internet_toggle, font=("Arial", 12, "bold"), progress_color="#10B981")
        self.internet_toggle.pack(side="left", padx=10, pady=10)
        self.internet_toggle.deselect()

        # Kombinerad Connect/Disconnect-knapp (Drivs via trigger_combined_adapter_action)
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
        self.matrix_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#1E293B")
        self.matrix_frame.pack(pady=5, padx=10, fill="x")

        matrix_title_str = self.localizer.get_text("matrix_title") if self.localizer else "CHANNEL CONTROL"
        self.matrix_title = ctk.CTkLabel(self.matrix_frame, text=matrix_title_str, font=("Arial", 11, "bold"), text_color="#94A3B8")
        self.matrix_title.pack(anchor="w", padx=15, pady=(8, 2))

        self.controls_grid = ctk.CTkFrame(self.matrix_frame, fg_color="transparent")
        self.controls_grid.pack(fill="x", padx=15, pady=(0, 10))

        # 3. POPULATE THE CONTROLS GRID
        chat_switch_str = self.localizer.get_text("chat_switch") if self.localizer else "Text Chat"
        self.chat_switch = ctk.CTkSwitch(self.controls_grid, text=chat_switch_str, command=self.sync_matrix_to_core, font=("Arial", 12), text_color="#E2E8F0")
        self.chat_switch.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.chat_switch.deselect()

        voice_label_str = self.localizer.get_text("voice_label") if self.localizer else "Voice Mode:"
        self.voice_label = ctk.CTkLabel(self.controls_grid, text=voice_label_str, font=("Arial", 12), text_color="#E2E8F0")
        self.voice_label.grid(row=0, column=1, padx=(20, 5), pady=10, sticky="w")

        voice_modes_list = self.localizer.get_voice_modes() if self.localizer else ["OFF", "PTT", "LISTEN"]
        self.voice_mode_btn = ctk.CTkSegmentedButton(self.controls_grid, values=voice_modes_list, command=self.on_voice_mode_change)
        self.voice_mode_btn.grid(row=0, column=2, padx=5, pady=10, sticky="w")

        # FIXED: Tvingar fram ett scalar-index för att permanent krossa unhashable type list-felet vid boot
        self.voice_mode_btn.set(voice_modes_list[0])

        tel_switch_str = self.localizer.get_text("telemetry_switch") if self.localizer else "Read Telemetry"
        self.read_telemetry_switch = ctk.CTkSwitch(self.controls_grid, text=tel_switch_str, command=self.on_telemetry_toggle, font=("Arial", 12), text_color="#E2E8F0")
        self.read_telemetry_switch.grid(row=0, column=3, padx=40, pady=10, sticky="w")
        self.read_telemetry_switch.deselect()

        write_switch_str = self.localizer.get_text("write_switch") if self.localizer else "Write to Adapter"
        self.write_adapter_switch = ctk.CTkSwitch(self.controls_grid, text=write_switch_str, command=self.sync_matrix_to_core, font=("Arial", 12), text_color="#E2E8F0")
        self.write_adapter_switch.grid(row=0, column=4, padx=20, pady=10, sticky="w")
        self.write_adapter_switch.deselect()

        # 4. CENTRAL TEXT STREAM LOG BOX
        self.log_box = ctk.CTkTextbox(self, font=("Consolas", 12), corner_radius=10)
        self.log_box.pack(pady=5, padx=10, fill="both", expand=True)
        log_ready_str = self.localizer.get_text("log_ready") if self.localizer else "READY.\n"
        self.log_box.insert("0.0", log_ready_str)
        self.log_box.configure(state="disabled")

        # VISUAL INTEGRATION: Skapar stilen för klickbara länkar direkt på loggboxens inre text-widget
        self.log_box.tag_config("hyperlink", foreground="#3B82F6", underline=True)
        
        # Binder händelser för att ändra muspekaren till en hand när man hovrar över länkar
        self.log_box.tag_bind("hyperlink", "<Enter>", lambda e: self.log_box.configure(cursor="hand2"))
        self.log_box.tag_bind("hyperlink", "<Leave>", lambda e: self.log_box.configure(cursor=""))

        # 5. LOWER FRAME INTERACTIVE INPUT CONTROLS
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(pady=10, padx=10, fill="x", side="bottom")

        placeholder_str = self.localizer.get_text("input_placeholder") if self.localizer else "Type message..."
        self.entry_field = ctk.CTkEntry(self.bottom_frame, placeholder_text=placeholder_str, font=("Arial", 12))
        self.entry_field.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_field.bind("<Return>", lambda event: self.trigger_text_input())

        send_str = self.localizer.get_text("send_btn") if self.localizer else "Send"
        self.send_button = ctk.CTkButton(self.bottom_frame, text=send_str, command=self.trigger_text_input, width=100)
        self.send_button.pack(side="right")

        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(pady=(0, 5), padx=10, fill="x", side="bottom")

        lock_str = self.localizer.get_text("lock_switch") if self.localizer else "Lock keyboard"
        self.lock_switch = ctk.CTkSwitch(self.control_frame, text=lock_str, command=self.on_lock_toggle)
        self.lock_switch.pack(side="left", padx=5)
        self.lock_switch.deselect()

        # FLYTTAD HIT: Stay-on-Top switch placeras nu direkt till höger om Keyboard Lock i bottenpanelen
        topmost_str = self.localizer.get_text("topmost_toggle") if self.localizer else "Stay on Top"
        self.topmost_toggle_switch = ctk.CTkSwitch(self.control_frame, text=topmost_str, command=self.on_topmost_toggle, font=("Arial", 12), progress_color="#3B82F6")
        self.topmost_toggle_switch.pack(side="left", padx=20)
        self.topmost_toggle_switch.select()

        hotkey_str = self.localizer.get_text("hotkey_btn") if self.localizer else "Set hotkey"
        self.hotkey_btn = ctk.CTkButton(self.control_frame, text=hotkey_str, command=self.start_hotkey_capture, width=180, fg_color="#374151", hover_color="#4B5563")
        self.hotkey_btn.pack(side="right", padx=5)

        # EXPANSION v3.5: Binder ett klick-event istället för dubbelklick för att göra det mycket mer intuitivt
        self.log_box.bind("<Button-1>", lambda event: function_handle_log_double_click(self, event))

        self.model_monitor.start_lamp_monitor(
            core_hub_callback=lambda: self.core_hub,
            update_lamp_ui_callback=self._safe_update_lamp_color,
            get_switch_state_callback=lambda: self.ai_toggle_switch.get()
        )
