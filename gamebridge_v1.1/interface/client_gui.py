# -*- coding: utf-8 -*-

"""
KOPPLINGAR:

- HÄMTAR FRÅN: interface/ui_event_queue.py,
  core/telemetry_core.py, core/model_monitor_core.py,
  interface/gui_functions.py, interface/chat_window.py,
  core/path_core.py
- ANROPAS AV: main/main.py
"""

import customtkinter as ctk
import threading

from core.path_core import PathCore
from interface.ui_event_queue import UIEventQueue
from core.model_monitor_core import ModelMonitorCore
from interface.chat_window import ChatWindow
from interface.gui_functions import (
    function_on_ai_toggle,
    function_on_internet_toggle,
    function_sync_matrix_to_core,
    function_on_telemetry_toggle,
    function_on_lock_toggle,
    function_on_model_change,
    function_on_adapter_change,
    function_trigger_text_input,
    function_open_external_link,
)


class GameBridgeGUI(ctk.CTk):

    def __init__(
        self,
        core_hub=None,
        matrix=None,
        localizer=None,
    ):
        super().__init__()

        self.core_hub = core_hub
        self.matrix = matrix
        self.localizer = localizer
        self.version = "1.1.0"

        self.event_queue = UIEventQueue()
        self.model_monitor = ModelMonitorCore()

        # Channel 1 / voice state
        # Sparar valt voice-läge när Channel 1 stängs av.
        self._channel1_voice_mode = None

        # ======================================================
        # CHAT GEOMETRY
        # ======================================================

        self.chat_base_width = 960
        self.chat_base_height = 540

        self.chat_border = 10

        self.chat_frame_base_width = (
            self.chat_base_width + (self.chat_border * 2)
        )

        self.chat_frame_base_height = (
            self.chat_base_height + (self.chat_border * 2)
        )

        self._resize_guard = False
        self._last_window_width = 0
        self._last_window_height = 0
        self._layout_ready = False

        self.attributes("-topmost", True)

        self._build_ui()
        self._process_gui_queue_loop()

    # ==========================================================
    # CALLBACKS
    # ==========================================================

    def on_ai_toggle(self):
        function_on_ai_toggle(self)

    def on_internet_toggle(self):
        function_on_internet_toggle(self)

    def on_topmost_toggle(self):
        if hasattr(self, "topmost_toggle_switch"):
            is_on = self.topmost_toggle_switch.get() == 1

            self.attributes("-topmost", is_on)

            state_msg = (
                "Always-on-Top activated."
                if is_on
                else (
                    "Always-on-Top deactivated. "
                    "Background persistence active."
                )
            )

            self.append_log("SYSTEM", state_msg)

    def sync_matrix_to_core(self):
        function_sync_matrix_to_core(self)

    def on_telemetry_toggle(self):
        function_on_telemetry_toggle(self)

    def on_lock_toggle(self):
        function_on_lock_toggle(self)

        if (
            hasattr(self, "lock_icon_label")
            and hasattr(self, "lock_switch")
        ):
            icon = (
                "⌨️🔒"
                if self.lock_switch.get() == 1
                else "⌨️🔓"
            )

            self.lock_icon_label.configure(text=icon)

    def on_voice_mode_change(self, mode):
        pass

    def _safe_update_lamp_color(self, color_hex: str):
        self.event_queue.dispatch(
            lambda: self.ai_status_lamp.configure(
                text_color=color_hex
            )
        )

    def start_hotkey_capture(self):
        if self.core_hub:
            self.hotkey_btn.configure(
                text="  ⌨️⏳",
                fg_color="#DC2626",
            )

            threading.Thread(
                target=self.core_hub.capture_new_hotkey,
                daemon=True,
            ).start()

    def on_model_change(self, selected_model):
        function_on_model_change(self, selected_model)

    @property
    def log_box(self):
        return self.chat_window.log_box

    @property
    def entry_field(self):
        return self.entry_field_widget

    def append_log(self, sender: str, text: str):
        """
        Central presentation gate for GUI traffic.

        Channel 1 controls presentation of AI Channel 1 traffic.
        Other system / telemetry / channel traffic is unaffected.

        Voice is handled separately by the existing bridge callback.
        """

        if sender == "AI (Channel 1)":
            if not hasattr(self, "chat_switch"):
                return

            if self.chat_switch.get() != 1:
                return

        self.chat_window.append_chat_message(sender, text)

    def _process_gui_queue_loop(self):
        self.event_queue.process_next_batch()

        self.after(
            50,
            self._process_gui_queue_loop,
        )

    def on_adapter_change(self, selected_adapter):
        function_on_adapter_change(self, selected_adapter)

        no_adapter_text = (
            self.localizer.get_text("no_adapter")
            if self.localizer
            else "No Adapter Loaded"
        )

        boot_str = (
            self.localizer.get_text("boot_btn")
            if self.localizer
            else "Launch / Attach App"
        )

        if selected_adapter == no_adapter_text:
            self.boot_target_btn.configure(
                text=boot_str,
                fg_color="#059669",
                hover_color="#10B981",
                state="disabled",
            )
        else:
            self.boot_target_btn.configure(
                text=boot_str,
                fg_color="#059669",
                hover_color="#10B981",
                state="normal",
            )

    def trigger_combined_adapter_action(self):
        no_adapter_text = (
            self.localizer.get_text("no_adapter")
            if self.localizer
            else "No Adapter Loaded"
        )

        disconnect_str = (
            self.localizer.get_text("disconnect_btn")
            if self.localizer
            else "Disconnect"
        )

        if self.boot_target_btn.cget("text") == disconnect_str:
            self.adapter_selector.set(no_adapter_text)
            self.on_adapter_change(no_adapter_text)

        else:
            if self.core_hub:
                self.append_log(
                    "SYSTEM",
                    "Initializing manual boot sequence...",
                )

                self.core_hub.boot_target_application()

            self.boot_target_btn.configure(
                text=disconnect_str,
                fg_color="#DC2626",
                hover_color="#EF4444",
            )

    def trigger_text_input(self):
        function_trigger_text_input(self)

    def on_text_size_toggle(self):
        is_large = self.text_size_switch.get() == 1

        self.chat_window.set_text_dimensions(is_large)

    def on_text_color_toggle(self):
        is_black = self.text_color_switch.get() == 1

        self.chat_window.set_text_mode_black(is_black)

    def toggle_monitor_panel(self):
        is_visible = self.monitor_switch.get() == 1

        self.chat_window.set_monitor_visibility(is_visible)

    # ==========================================================
    # CHAT SCROLLBAR
    # ==========================================================

    def _connect_chat_scrollbar(self):
        """
        Kopplar client_gui:s scrollbar till ChatWindows
        HtmlFrame.

        Scrollbaren ägs av client_gui.

        ChatWindow äger presentationen.

        Själva scrollpositionen hanteras av HtmlFrame.
        """

        try:

            self.chat_scrollbar.configure(
                command=self.chat_window.html_viewer.yview
            )


        except Exception as e:

            print(
                "[GUI-SCROLL] "
                f"Failed to connect chat scrollbar: {e}"
            )

    # ==========================================================
    # GEOMETRY MEASUREMENT
    # ==========================================================

    def _measure_vertical_overhead(self):
        """
        Mäter allt som ligger utanför chatramen.

        Chatramen är den geometriska referensen.
        """

        self.update_idletasks()

        window_h = max(1, self.winfo_height())
        chat_frame_h = max(1, self.chat_frame.winfo_height())

        overhead = window_h - chat_frame_h

        return max(0, overhead)

    def _measure_horizontal_overhead(self):
        """
        Mäter faktisk breddskillnad mellan fönstret
        och chatramen.
        """

        self.update_idletasks()

        window_w = max(1, self.winfo_width())
        chat_frame_w = max(1, self.chat_frame.winfo_width())

        overhead = window_w - chat_frame_w

        return max(0, overhead)

    def _set_geometry_from_chat_width(
        self,
        chat_width,
        horizontal_overhead,
        vertical_overhead,
    ):
        """
        Räknar hela fönstrets storlek från chatbredden.
        """

        chat_width = max(
            self.chat_base_width,
            int(chat_width),
        )

        chat_height = int(
            round(chat_width * 9.0 / 16.0)
        )

        frame_width = (
            chat_width + (self.chat_border * 2)
        )

        frame_height = (
            chat_height + (self.chat_border * 2)
        )

        total_width = (
            frame_width + horizontal_overhead
        )

        total_height = (
            frame_height + vertical_overhead
        )

        self.geometry(
            f"{total_width}x{total_height}"
        )

    def _on_root_resize(self, event):
        """
        Root-fönstrets geometriska controller.

        Chatramen är den geometriska referensen.

        Vertikal ankarkedja:

            TOP
              ↓
            MATRIX
              ↓
            CHAT
              ↓
            INPUT
              ↓
            CONTROL

        Relationerna är:

            TOP SW      -> CHAT NW
            CHAT SW     -> INPUT NW
            INPUT SW    -> CONTROL NW

        Endast chattytan är låst till 16:9.
        """

        if event.widget is not self:
            return

        if not self._layout_ready:
            return

        if self._resize_guard:
            return

        current_w = self.winfo_width()
        current_h = self.winfo_height()

        if (
            current_w == self._last_window_width
            and current_h == self._last_window_height
        ):
            return

        self._resize_guard = True

        try:

            horizontal_overhead = (
                self._measure_horizontal_overhead()
            )

            vertical_overhead = (
                self._measure_vertical_overhead()
            )

            candidate_frame_w = max(
                self.chat_frame_base_width,
                current_w - horizontal_overhead,
            )

            candidate_frame_h = max(
                self.chat_frame_base_height,
                current_h - vertical_overhead,
            )

            candidate_chat_w = (
                candidate_frame_w
                - (self.chat_border * 2)
            )

            candidate_chat_h = (
                candidate_frame_h
                - (self.chat_border * 2)
            )

            previous_w = self._last_window_width
            previous_h = self._last_window_height

            delta_w = abs(current_w - previous_w)
            delta_h = abs(current_h - previous_h)

            if delta_w >= delta_h:

                target_chat_w = max(
                    self.chat_base_width,
                    candidate_chat_w,
                )

                target_chat_h = int(
                    round(target_chat_w * 9.0 / 16.0)
                )

            else:

                target_chat_h = max(
                    self.chat_base_height,
                    candidate_chat_h,
                )

                target_chat_w = int(
                    round(target_chat_h * 16.0 / 9.0)
                )

            target_frame_w = (
                target_chat_w + (self.chat_border * 2)
            )

            target_frame_h = (
                target_chat_h + (self.chat_border * 2)
            )

            target_window_w = (
                target_frame_w + horizontal_overhead
            )

            target_window_h = (
                target_frame_h + vertical_overhead
            )

            # --------------------------------------------------
            # CHAT FRAME
            # --------------------------------------------------

            self.chat_frame.configure(
                width=target_frame_w,
                height=target_frame_h,
            )

            # --------------------------------------------------
            # CHAT
            # --------------------------------------------------

            self.chat_window.configure(
                width=target_chat_w,
                height=target_chat_h,
            )

            # --------------------------------------------------
            # SCROLLBAR
            #
            # Hålls ovanpå presentationen och följer
            # ChatWindows 16:9-yta.
            # --------------------------------------------------

            if hasattr(
                self,
                "chat_scrollbar"
            ):

                self.chat_scrollbar.place(
                    relx=1.0,
                    x=-self.chat_border,
                    y=self.chat_border,
                    anchor="ne",
                    relheight=1.0,
                )

            # --------------------------------------------------
            # ROOT
            # --------------------------------------------------

            if (
                target_window_w != current_w
                or target_window_h != current_h
            ):

                self.geometry(
                    f"{target_window_w}x"
                    f"{target_window_h}"
                )

            self._last_window_width = target_window_w
            self._last_window_height = target_window_h

        finally:

            self.after_idle(
                self._release_resize_guard
            )

    def _release_resize_guard(self):
        self._resize_guard = False

    # ==========================================================
    # BUILD UI
    # ==========================================================

    def _build_ui(self):

        title_str = (
            self.localizer.get_text("title")
            if self.localizer
            else "G.A.M.E. B.R.I.D.G.E."
        )

        self.title(title_str)

        # ======================================================
        # MAIN CONTAINER
        # ======================================================

        self.main_container = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )

        self.main_container.pack(
            fill="both",
            expand=True,
        )

        self.main_container.grid_columnconfigure(
            0,
            weight=1,
        )

        for row in range(5):
            self.main_container.grid_rowconfigure(
                row,
                weight=0,
            )

        # ======================================================
        # TOP PANEL
        # ======================================================

        self.top_frame = ctk.CTkFrame(
            self.main_container,
            corner_radius=10,
        )

        self.top_frame.grid(
            row=0,
            column=0,
            padx=10,
            pady=(10, 5),
            sticky="ew",
        )

        self.ai_status_lamp = ctk.CTkLabel(
            self.top_frame,
            text="●",
            text_color="#9CA3AF",
            font=("Arial", 22),
        )

        self.ai_status_lamp.pack(
            side="left",
            padx=(15, 5),
            pady=10,
        )

        status_str = (
            self.localizer.get_text("status_ready")
            if self.localizer
            else "Status: Ready"
        )

        self.status_label = ctk.CTkLabel(
            self.top_frame,
            text=status_str,
            font=("Arial", 13, "bold"),
        )

        self.status_label.pack(
            side="left",
            padx=5,
            pady=10,
        )

        ai_toggle_str = (
            self.localizer.get_text("ai_toggle")
            if self.localizer
            else "AI Active"
        )

        self.ai_toggle_switch = ctk.CTkSwitch(
            self.top_frame,
            text=ai_toggle_str,
            command=self.on_ai_toggle,
            font=("Arial", 12, "bold"),
        )

        self.ai_toggle_switch.pack(
            side="left",
            padx=10,
            pady=10,
        )

        self.ai_toggle_switch.deselect()

        internet_toggle_str = (
            self.localizer.get_text("internet_toggle")
            if self.localizer
            else "Internet AI"
        )

        self.internet_toggle = ctk.CTkSwitch(
            self.top_frame,
            text=internet_toggle_str,
            command=self.on_internet_toggle,
            font=("Arial", 12, "bold"),
            progress_color="#10B981",
        )

        self.internet_toggle.pack(
            side="left",
            padx=10,
            pady=10,
        )

        self.internet_toggle.deselect()

        boot_str = (
            self.localizer.get_text("boot_btn")
            if self.localizer
            else "Launch / Attach App"
        )

        self.boot_target_btn = ctk.CTkButton(
            self.top_frame,
            text=boot_str,
            command=self.trigger_combined_adapter_action,
            width=150,
            fg_color="#059669",
            hover_color="#10B981",
            state="disabled",
        )

        self.boot_target_btn.pack(
            side="right",
            padx=(15, 15),
            pady=10,
        )

        no_adapter_text = (
            self.localizer.get_text("no_adapter")
            if self.localizer
            else "No Adapter Loaded"
        )

        initial_adapters = [no_adapter_text]

        if (
            self.core_hub
            and hasattr(self.core_hub, "available_adapters")
        ):

            discovered = list(
                self.core_hub.available_adapters.keys()
            )

            if discovered:
                initial_adapters.extend(discovered)

        self.adapter_selector = ctk.CTkOptionMenu(
            self.top_frame,
            values=initial_adapters,
            command=self.on_adapter_change,
        )

        self.adapter_selector.pack(
            side="right",
            padx=10,
            pady=10,
        )

        self.adapter_selector.set(
            no_adapter_text
        )

        self.model_selector = ctk.CTkOptionMenu(
            self.top_frame,
            values=self.model_monitor.fetch_installed_models(),
            command=self.on_model_change,
        )

        self.model_selector.pack(
            side="right",
            padx=10,
            pady=10,
        )

        if (
            self.core_hub
            and hasattr(self.core_hub, "global_config")
        ):

            saved_model = self.core_hub.global_config.get(
                "ai_model_name",
                "sailwind-pilot",
            )

            if saved_model in self.model_selector.cget(
                "values"
            ):

                self.model_selector.set(
                    saved_model
                )

        # ======================================================
        # CHANNEL MATRIX
        # ======================================================

        self.matrix_frame = ctk.CTkFrame(
            self.main_container,
            corner_radius=10,
            fg_color="#1E293B",
        )

        self.matrix_frame.grid(
            row=1,
            column=0,
            padx=10,
            pady=5,
            sticky="ew",
        )

        matrix_title_str = (
            self.localizer.get_text("matrix_title")
            if self.localizer
            else "CHANNEL CONTROL"
        )

        self.matrix_title = ctk.CTkLabel(
            self.matrix_frame,
            text=matrix_title_str,
            font=("Arial", 11, "bold"),
            text_color="#94A3B8",
        )

        self.matrix_title.pack(
            anchor="w",
            padx=15,
            pady=(8, 2),
        )

        self.controls_grid = ctk.CTkFrame(
            self.matrix_frame,
            fg_color="transparent",
        )

        self.controls_grid.pack(
            fill="x",
            padx=15,
            pady=(0, 10),
        )

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

        self.chat_switch.grid(
            row=0,
            column=0,
            padx=20,
            pady=10,
            sticky="w",
        )

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
            row=0,
            column=1,
            padx=(20, 5),
            pady=10,
            sticky="w",
        )

        voice_modes_list = [
            "  🔇 ",
            "🔘🎙️",
            "  🎙️ ",
        ]

        voice_mode_values = [
            "OFF",
            "PTT",
            "LISTEN",
        ]

        self.voice_mode_btn = ctk.CTkSegmentedButton(
            self.controls_grid,
            values=voice_modes_list,
            command=lambda mode: self.on_voice_mode_change(
                voice_mode_values[
                    voice_modes_list.index(mode)
                ]
            ),
            font=("Arial", 14),
            selected_color="#3B82F6",
        )

        self.voice_mode_btn.grid(
            row=0,
            column=2,
            padx=5,
            pady=10,
            sticky="w",
        )

        self.voice_mode_btn.set(
            voice_modes_list[0]
        )

        def _update_voice_btn_color(mode):

            if mode == "  🔇 ":

                self.voice_mode_btn.configure(
                    selected_color="#DC2626",
                    font=("Arial", 16),
                )

            elif mode == "🔘🎙️":

                self.voice_mode_btn.configure(
                    selected_color="#059669",
                    font=("Arial", 14),
                )

            elif mode == "  🎙️ ":

                self.voice_mode_btn.configure(
                    selected_color="#059669",
                    font=("Arial", 16),
                )

        orig_voice_change = self.on_voice_mode_change

        def _wrapped_voice_change(mode):

            _update_voice_btn_color(mode)
            orig_voice_change(mode)

        self.voice_mode_btn.configure(
            command=_wrapped_voice_change
        )

        _update_voice_btn_color(
            voice_modes_list[0]
        )

        tel_switch_str = (
            self.localizer.get_text("telemetry_switch")
            if self.localizer
            else "Read Telemetry"
        )

        self.read_telemetry_switch = ctk.CTkSwitch(
            self.controls_grid,
            text=tel_switch_str,
            command=self.on_telemetry_toggle,
            font=("Arial", 12),
            text_color="#E2E8F0",
        )

        self.read_telemetry_switch.grid(
            row=0,
            column=3,
            padx=40,
            pady=10,
            sticky="w",
        )

        self.read_telemetry_switch.deselect()

        write_switch_str = (
            self.localizer.get_text("write_switch")
            if self.localizer
            else "Write to Adapter"
        )

        self.write_adapter_switch = ctk.CTkSwitch(
            self.controls_grid,
            text=write_switch_str,
            command=self.sync_matrix_to_core,
            font=("Arial", 12),
            text_color="#E2E8F0",
        )

        self.write_adapter_switch.grid(
            row=0,
            column=4,
            padx=20,
            pady=10,
            sticky="w",
        )

        self.write_adapter_switch.deselect()

        # ======================================================
        # CHAT FRAME
        #
        # EXAKT 980 x 560 vid basstorlek.
        #
        # Själva ChatWindow är 960 x 540.
        #
        # Chat frame är geometriskt ankare för chatten.
        # ======================================================

        self.chat_frame = ctk.CTkFrame(
            self.main_container,
            width=self.chat_frame_base_width,
            height=self.chat_frame_base_height,
            fg_color="#10172A",
        )

        self.chat_frame.grid(
            row=2,
            column=0,
            padx=10,
            pady=5,
            sticky="nw",
        )

        self.chat_frame.grid_propagate(False)

        # ------------------------------------------------------
        # CHAT PRESENTATION
        # ------------------------------------------------------

        self.chat_window = ChatWindow(
            master=self.chat_frame,
            localizer=self.localizer,
            handle_log_click_callback=function_open_external_link,
            width=self.chat_base_width,
            height=self.chat_base_height,
        )

        self.chat_window.place(
            x=self.chat_border,
            y=self.chat_border,
        )

        # ------------------------------------------------------
        # CHAT SCROLLBAR
        #
        # Scrollbaren ägs av client_gui.
        #
        # Den placeras ovanpå ChatWindow så att användaren
        # kan komma åt presentationens scroll utan att först
        # behöva markera HTML-texten.
        #
        # Själva scrollmotorn ligger fortfarande i ChatWindow
        # genom HtmlFrame.yview().
        # ------------------------------------------------------

        self.chat_scrollbar = ctk.CTkScrollbar(
            self.chat_frame,
            orientation="vertical",
        )

        self.chat_scrollbar.place(
            relx=1.0,
            x=-self.chat_border,
            y=self.chat_border,
            anchor="ne",
            relheight=1.0,
        )

        self._connect_chat_scrollbar()

        # ======================================================
        # BOTTOM INPUT
        #
        # CHAT SW -> INPUT NW
        #
        # INPUT ligger direkt EFTER chatten.
        # ======================================================

        self.bottom_input_frame = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent",
        )

        self.bottom_input_frame.grid(
            row=3,
            column=0,
            padx=10,
            pady=(5, 10),
            sticky="ew",
        )

        placeholder_str = (
            self.localizer.get_text("input_placeholder")
            if self.localizer
            else "Type message..."
        )

        self.entry_field_widget = ctk.CTkEntry(
            self.bottom_input_frame,
            placeholder_text=placeholder_str,
            font=("Arial", 12),
        )

        self.entry_field_widget.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10),
        )

        self.entry_field_widget.bind(
            "<Return>",
            lambda event: self.trigger_text_input(),
        )

        send_str = (
            self.localizer.get_text("send_btn")
            if self.localizer
            else "Send"
        )

        self.send_button = ctk.CTkButton(
            self.bottom_input_frame,
            text=send_str,
            command=self.trigger_text_input,
            width=100,
        )

        self.send_button.pack(
            side="right"
        )

        # ======================================================
        # BOTTOM CONTROL
        #
        # INPUT SW -> CONTROL NW
        #
        # CONTROL ligger SIST, alltså längst ned.
        # ======================================================

        self.control_frame = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent",
        )

        self.control_frame.grid(
            row=4,
            column=0,
            padx=10,
            pady=(0, 5),
            sticky="ew",
        )

        self.lock_icon_label = ctk.CTkLabel(
            self.control_frame,
            text="⌨️🔓",
            font=("Arial", 16),
        )

        self.lock_icon_label.pack(
            side="left",
            padx=(5, 2),
        )

        self.lock_switch = ctk.CTkSwitch(
            self.control_frame,
            text="",
            command=self.on_lock_toggle,
            width=45,
        )

        self.lock_switch.pack(
            side="left",
            padx=(0, 15),
        )

        self.lock_switch.deselect()

        orig_lock_toggle = self.on_lock_toggle

        def _wrapped_lock_toggle():

            orig_lock_toggle()

            icon = (
                "⌨️🔒"
                if self.lock_switch.get() == 1
                else "⌨️🔓"
            )

            self.lock_icon_label.configure(
                text=icon
            )

        self.lock_switch.configure(
            command=_wrapped_lock_toggle
        )

        topmost_str = (
            self.localizer.get_text("topmost_toggle")
            if self.localizer
            else "Stay on Top"
        )

        self.topmost_toggle_switch = ctk.CTkSwitch(
            self.control_frame,
            text=topmost_str,
            command=self.on_topmost_toggle,
            font=("Arial", 12),
            progress_color="#3B82F6",
        )

        self.topmost_toggle_switch.pack(
            side="left",
            padx=10,
        )

        self.topmost_toggle_switch.select()

        self.text_size_switch = ctk.CTkSwitch(
            self.control_frame,
            text="🔍 Stor text",
            command=self.on_text_size_toggle,
        )

        self.text_size_switch.pack(
            side="left",
            padx=10,
        )

        self.text_color_switch = ctk.CTkSwitch(
            self.control_frame,
            text="● Svart text",
            command=self.on_text_color_toggle,
        )

        self.text_color_switch.pack(
            side="left",
            padx=10,
        )

        self.text_color_switch.deselect()

        self.monitor_switch = ctk.CTkSwitch(
            self.control_frame,
            text="● K2 Mon",
            command=self.toggle_monitor_panel,
        )

        self.monitor_switch.pack(
            side="left",
            padx=10,
        )

        self.hotkey_btn = ctk.CTkButton(
            self.control_frame,
            text="  🔘🎙️",
            command=self.start_hotkey_capture,
            width=65,
            font=("Arial", 16, "bold"),
            fg_color="#374151",
            hover_color="#4B5563",
        )

        self.hotkey_btn.pack(
            side="right",
            padx=5,
        )

        # ======================================================
        # INITIAL GEOMETRY
        # ======================================================

        self.update_idletasks()

        requested_main_width = (
            self.main_container.winfo_reqwidth()
        )

        requested_main_height = (
            self.main_container.winfo_reqheight()
        )

        minimum_width = max(
            self.chat_frame_base_width + 20,
            requested_main_width,
        )

        minimum_height = max(
            self.chat_frame_base_height + 20,
            requested_main_height,
        )

        self.minsize(
            minimum_width,
            minimum_height,
        )

        self.geometry(
            f"{minimum_width}x"
            f"{minimum_height}"
        )

        self.update_idletasks()

        self._last_window_width = self.winfo_width()
        self._last_window_height = self.winfo_height()

        self._layout_ready = True

        self.bind(
            "<Configure>",
            self._on_root_resize,
        )

        print(
            "[GUI-GEOMETRY]",
            "chat=",
            self.chat_base_width,
            "x",
            self.chat_base_height,
            "| frame=",
            self.chat_frame_base_width,
            "x",
            self.chat_frame_base_height,
            "| requested=",
            requested_main_width,
            "x",
            requested_main_height,
            "| minimum=",
            minimum_width,
            "x",
            minimum_height,
        )

        print(
            "[GUI-ANCHOR]",
            "TOP SW -> CHAT NW",
        )

        print(
            "[GUI-ANCHOR]",
            "CHAT SW -> INPUT NW",
        )

        print(
            "[GUI-ANCHOR]",
            "INPUT SW -> CONTROL NW",
        )

        print(
            "[GUI-SCROLL]",
            "client_gui scrollbar -> ChatWindow HtmlFrame",
        )

        # ======================================================
        # MODEL MONITOR
        # ======================================================

        self.model_monitor.start_lamp_monitor(
            core_hub_callback=lambda: self.core_hub,
            update_lamp_ui_callback=self._safe_update_lamp_color,
            get_switch_state_callback=lambda:
                self.ai_toggle_switch.get(),
        )