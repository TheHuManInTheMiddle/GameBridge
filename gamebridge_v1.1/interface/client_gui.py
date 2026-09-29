# -*- coding: utf-8 -*-

"""
CONNECTIONS:

- FETCHES FROM: interface/ui_event_queue.py,
  core/telemetry_core.py, core/model_monitor_core.py,
  interface/gui_functions.py, interface/chat_window.py,
  interface/plugin_warning_frame.py, interface/settings_window.py
- CALLED BY: main/main.py
"""

import customtkinter as ctk
import threading

from core.runtime_state_core import RuntimeStateCore
from interface.ui_event_queue import UIEventQueue
from core.model_monitor_core import ModelMonitorCore
from interface.chat_window import ChatWindow
from interface.color_picker import ColorPicker
from interface.plugin_warning_frame import PluginWarningFrame
from interface.settings_window import SettingsWindow
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
        self.runtime_state = (
            self.core_hub.runtime_state
            if self.core_hub
            else RuntimeStateCore()
        )

        # Channel 1 / voice state.
        self._channel1_voice_mode = None

        # Fixed geometry.
        #
        # ChatWindow resizing caused visual tearing, so the
        # complete GameBridge window now uses a fixed size.
        self.chat_base_width = 960
        self.chat_base_height = 540
        self.chat_border = 10

        self.chat_frame_base_width = (
            self.chat_base_width + (self.chat_border * 2)
        )

        self.chat_frame_base_height = (
            self.chat_base_height + (self.chat_border * 2)
        )

        self.attributes("-topmost", False)

        self._build_ui()

        self._check_duplicate_plugin_warning()

        self._process_gui_queue_loop()

    # ==========================================================
    # LOCALIZATION HELPERS
    # ==========================================================

    def _get_localized_text(self, key, fallback):
        """
        Returns localized text when available.

        If the locale key does not exist yet, the fallback keeps
        the GUI functional until the locale file is updated.
        """

        if not self.localizer:
            return fallback

        try:
            value = self.localizer.get_text(key)

            if value and value != key:
                return value

        except Exception:
            pass

        return fallback

    # ==========================================================
    # CALLBACKS
    # ==========================================================

    def on_ai_toggle(self):
        self.runtime_state.set_state(
            "ai_active",
            self.ai_toggle_switch.get() == 1
        )

        function_on_ai_toggle(self)

        ai_active = self.runtime_state.get_state(
            "ai_active"
        )

        self.model_selector.configure(
            state="disabled" if ai_active else "normal"
        )

    def on_internet_toggle(self):
        self.runtime_state.set_state(
            "internet_ai_active",
            self.internet_toggle.get() == 1
        )

        function_on_internet_toggle(self)

    def on_memory_toggle(self):
        # Placeholder until the Memory function is implemented.
        self.memory_toggle_switch.deselect()

    def on_settings_open(self):
        if hasattr(self, "_settings_window"):
            try:
                if self._settings_window.winfo_exists():
                    self._settings_window.focus_force()
                    return
            except Exception:
                pass

        self._settings_window = SettingsWindow(
            parent=self,
            core_hub=self.core_hub,
            localizer=self.localizer,
            runtime_state=self.runtime_state,
        )

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
        self.runtime_state.set_state(
            "channel1_active",
            self.chat_switch.get() == 1
        )

        self.runtime_state.set_state(
            "ai_channel1_active",
            self.ai_chat_switch.get() == 1
        )

        self.runtime_state.set_state(
            "channel2_active",
            self.write_adapter_switch.get() == 1
        )

        function_sync_matrix_to_core(self)

    def on_telemetry_toggle(self):
        self.runtime_state.set_state(
            "telemetry_active",
            self.read_telemetry_switch.get() == 1
        )

        function_on_telemetry_toggle(self)

    def on_user_voice_toggle(self):
        self.runtime_state.set_state(
            "user_voice_active",
            self.voice_user_switch.get() == 1
        )

        function_sync_matrix_to_core(self)

    def on_ai_voice_toggle(self):
        self.runtime_state.set_state(
            "ai_voice_active",
            self.voice_ai_switch.get() == 1
        )

        function_sync_matrix_to_core(self)

    def on_lock_toggle(self):
        self.runtime_state.set_state(
            "locked",
            self.lock_switch.get() == 1
        )

        function_on_lock_toggle(self)

        if (
            hasattr(self, "lock_icon_label")
            and hasattr(self, "lock_switch")
        ):
            icon = (
                self._get_localized_text(
                    "icon_tgblock_locked",
                    "TGBLOCK_LOCKED",
                )
                if self.runtime_state.get_state("locked")
                else self._get_localized_text(
                    "icon_tgblock_unlocked",
                    "TGBLOCK_UNLOCKED",
                )
            )

            self.lock_icon_label.configure(
                text=icon
            )

    def on_voice_mode_change(self, mode):
        self.runtime_state.set_state(
            "voice_mode",
            mode
        )

    def _safe_update_lamp_color(self, color_hex: str):
        self.event_queue.dispatch(
            lambda: self.ai_status_lamp.configure(
                text_color=color_hex
            )
        )

    def start_hotkey_capture(self):
        if self.core_hub:
            self.hotkey_btn.configure(
                text=self._get_localized_text(
                    "icon_ptt_hotkey_capture",
                    "PTT_HOTKEY_CAPTURE",
                ),
                fg_color="#DC2626",
            )

            threading.Thread(
                target=self.core_hub.capture_new_hotkey,
                daemon=True,
            ).start()

    def refresh_ai_provider(self, provider_name):
        """Refresh the active AI provider model list at runtime."""

        model_values = (
            self.model_monitor.fetch_installed_models(
                provider_name
            )
        )

        self.model_selector.configure(
            values=model_values
        )

        self.model_selector.set(
            model_values[0]
        )

    def on_model_change(self, selected_model):
        function_on_model_change(
            self,
            selected_model
        )

    @property
    def log_box(self):
        return self.chat_window.log_box

    @property
    def entry_field(self):
        return self.entry_field_widget

    def append_log(self, sender: str, text: str):
        """
        Central presentation gate for GUI traffic.

        User Channel 1 and AI Channel 1 are independent
        presentation paths.

        Voice is handled separately by the existing bridge callback.
        """

        if sender == "AI (Channel 1)":
            if not hasattr(self, "ai_chat_switch"):
                return

            if self.ai_chat_switch.get() != 1:
                return

        self.chat_window.append_chat_message(
            sender,
            text
        )

    def _process_gui_queue_loop(self):
        self.event_queue.process_next_batch()

        self.after(
            50,
            self._process_gui_queue_loop,
        )

    def on_adapter_change(self, selected_adapter):
        function_on_adapter_change(
            self,
            selected_adapter
        )

        no_adapter_text = self._get_localized_text(
            "no_adapter",
            "No Adapter Loaded",
        )

        if selected_adapter == no_adapter_text:
            self.runtime_state.set_state(
                "channel2_active",
                False
            )

        boot_str = self._get_localized_text(
            "boot_btn",
            "Launch / Attach App",
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
        no_adapter_text = self._get_localized_text(
            "no_adapter",
            "No Adapter Loaded",
        )

        disconnect_str = self._get_localized_text(
            "disconnect_btn",
            "Disconnect",
        )

        if self.boot_target_btn.cget("text") == disconnect_str:
            self.adapter_selector.set(
                no_adapter_text
            )

            self.on_adapter_change(
                no_adapter_text
            )

            self.adapter_selector.configure(
                state="normal"
            )

        else:
            if self.core_hub:
                self.append_log(
                    "SYSTEM",
                    "Initializing manual boot sequence...",
                )

                self.core_hub.boot_target_application()

            adapter = self.core_hub.active_adapter_instance

            if adapter and adapter.plugin_allow_ch2:
                self.write_adapter_switch.configure(
                    state="normal"
                )

            if adapter and adapter.plugin_allow_telemetry:
                self.read_telemetry_switch.configure(
                    state="normal"
                )

            self.boot_target_btn.configure(
                text=disconnect_str,
                fg_color="#DC2626",
                hover_color="#EF4444",
            )

            self.adapter_selector.configure(
                state="disabled"
            )

    def trigger_text_input(self):
        function_trigger_text_input(self)

    def on_text_size_toggle(self):
        is_large = self.text_size_switch.get() == 1

        self.chat_window.set_text_dimensions(
            is_large
        )

    def open_text_color_picker(self):
        current_color = "#FFFFFF"

        if hasattr(
            self.chat_window,
            "text_color"
        ):
            current_color = self.chat_window.text_color

        if (
            hasattr(
                self,
                "_color_picker"
            )
        ):
            try:
                if self._color_picker.winfo_exists():
                    self._color_picker.focus_force()
                    return
            except Exception:
                pass

        self._color_picker = ColorPicker(
            parent=self,
            current_color=current_color,
            callback=self.on_text_color_selected,
        )

        self._color_picker.geometry(
            "300x210"
        )

        self._color_picker.update_idletasks()

    def on_text_color_selected(self, color):
        selected_color = str(
            color
        ).strip().upper()

        if not selected_color:
            return

        self.chat_window.set_text_color(
            selected_color
        )

        if (
            self.core_hub
            and hasattr(
                self.core_hub,
                "global_config"
            )
            and hasattr(
                self.core_hub,
                "config_manager"
            )
        ):
            self.core_hub.global_config[
                "chat_text_color"
            ] = selected_color

            self.core_hub.config_manager.save_global_config(
                self.core_hub.global_config
            )

    def toggle_monitor_panel(self):
        is_visible = self.monitor_switch.get() == 1

        self.chat_window.set_monitor_visibility(
            is_visible
        )

    # ==========================================================
    # DUPLICATE PLUGIN WARNING
    # ==========================================================

    def _check_duplicate_plugin_warning(self):
        """
        Checks whether AdapterLoader has registered
        a conflict between main_adapter.py and .gbp.

        The warning dialog is shown only when an actual
        conflict exists.
        """

        duplicate_plugin = (
            self.runtime_state.get_state(
                "duplicate_plugin",
                False
            )
        )

        if not duplicate_plugin:
            return

        self._duplicate_plugin_window = ctk.CTkToplevel(
            self
        )

        title = self._get_localized_text(
            "duplicate_plugin_title",
            "Duplicate plugin detected",
        )

        self._duplicate_plugin_window.title(
            title
        )

        self._duplicate_plugin_window.resizable(
            False,
            False
        )

        self._duplicate_plugin_window.transient(
            self
        )

        self._duplicate_plugin_window.grab_set()

        warning_frame = PluginWarningFrame(
            self._duplicate_plugin_window,
            runtime_state=self.runtime_state,
            core_hub=self.core_hub,
            localizer=self.localizer
        )

        warning_frame.pack(
            padx=5,
            pady=5
        )

        self._duplicate_plugin_window.update_idletasks()

        window_width = (
            warning_frame.winfo_reqwidth() + 10
        )

        window_height = (
            warning_frame.winfo_reqheight() + 10
        )

        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()

        parent_width = self.winfo_width()
        parent_height = self.winfo_height()

        x = (
            parent_x
            + (parent_width - window_width) // 2
        )

        y = (
            parent_y
            + (parent_height - window_height) // 2
        )

        self._duplicate_plugin_window.geometry(
            f"{window_width}x"
            f"{window_height}+{x}+{y}"
        )

        self._duplicate_plugin_window.focus_force()

    # ==========================================================
    # CHAT SCROLLBAR
    # ==========================================================

    def _connect_chat_scrollbar(self):
        """
        Connects the client GUI scrollbar to ChatWindow.

        The scrollbar is owned by client_gui.

        ChatWindow owns the presentation and scrolling engine.
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
    # BUILD UI
    # ==========================================================

    def _build_ui(self):

        title_str = self._get_localized_text(
            "title",
            "G.A.M.E. B.R.I.D.G.E.",
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

        status_icon = self._get_localized_text(
            "icon_status_indicator",
            "STATUS_INDICATOR",
        )

        self.ai_status_lamp = ctk.CTkLabel(
            self.top_frame,
            text=status_icon,
            text_color="#9CA3AF",
            font=("Arial", 22),
        )

        self.ai_status_lamp.pack(
            side="left",
            padx=(15, 5),
            pady=10,
        )

        status_str = self._get_localized_text(
            "status",
            "Status",
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

        ai_toggle_str = self._get_localized_text(
            "ai_toggle",
            "AI Active",
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

        internet_toggle_str = self._get_localized_text(
            "internet_toggle",
            "Internet AI",
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

        memory_str = self._get_localized_text(
            "memory_toggle",
            "Memory",
        )

        self.memory_toggle_switch = ctk.CTkSwitch(
            self.top_frame,
            text=memory_str,
            command=self.on_memory_toggle,
            font=("Arial", 12, "bold"),
        )

        self.memory_toggle_switch.pack(
            side="left",
            padx=10,
            pady=10,
        )

        self.memory_toggle_switch.deselect()

        boot_str = self._get_localized_text(
            "boot_btn",
            "Launch / Attach App",
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

        no_adapter_text = self._get_localized_text(
            "no_adapter",
            "No Adapter Loaded",
        )

        initial_adapters = [no_adapter_text]

        if (
            self.core_hub
            and hasattr(
                self.core_hub,
                "available_adapters"
            )
        ):
            discovered = list(
                self.core_hub.available_adapters.keys()
            )

            if discovered:
                initial_adapters.extend(
                    discovered
                )

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

        ai_provider = "none"

        if (
            self.core_hub
            and hasattr(
                self.core_hub,
                "global_config"
            )
        ):
            ai_provider = self.core_hub.global_config.get(
                "ai_provider",
                "none",
            )

        self.model_selector = ctk.CTkOptionMenu(
            self.top_frame,
            values=self.model_monitor.fetch_installed_models(
                ai_provider
            ),
            command=self.on_model_change,
        )

        self.model_selector.pack(
            side="right",
            padx=10,
            pady=10,
        )

        if (
            self.core_hub
            and hasattr(
                self.core_hub,
                "global_config"
            )
        ):
            saved_model = self.core_hub.global_config.get(
                "ai_model_name",
                "none",
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

        self.controls_grid = ctk.CTkFrame(
            self.matrix_frame,
            fg_color="transparent",
        )

        self.controls_grid.pack(
            fill="x",
            padx=15,
            pady=(8, 10),
        )

        # ======================================================
        # MATRIX GRID
        #
        # 0 = User Channel 1
        # 1 = User Voice
        # 2 = Voice Mode
        # 3 = AI Voice
        # 4 = AI Channel 1
        # 5 = Telemetry
        # 6 = Channel 2
        #
        # Voice Mode label has been removed.
        # The VOICE section title already identifies the control.
        # ======================================================

        self.controls_grid.grid_columnconfigure(
            0,
            weight=1,
            minsize=120,
        )

        self.controls_grid.grid_columnconfigure(
            1,
            weight=1,
            minsize=120,
        )

        self.controls_grid.grid_columnconfigure(
            2,
            weight=2,
            minsize=170,
        )

        self.controls_grid.grid_columnconfigure(
            3,
            weight=1,
            minsize=120,
        )

        self.controls_grid.grid_columnconfigure(
            4,
            weight=1,
            minsize=120,
        )

        self.controls_grid.grid_columnconfigure(
            5,
            weight=1,
            minsize=130,
        )

        self.controls_grid.grid_columnconfigure(
            6,
            weight=1,
            minsize=130,
        )

        self.controls_grid.grid_rowconfigure(
            0,
            weight=0,
        )

        self.controls_grid.grid_rowconfigure(
            1,
            weight=0,
        )

        # ======================================================
        # SECTION LABELS
        # ======================================================

        user_channels_title = self._get_localized_text(
            "matrix_user_channels",
            "USER CHANNELS",
        )

        self.user_channels_title = ctk.CTkLabel(
            self.controls_grid,
            text=user_channels_title,
            font=("Arial", 10, "bold"),
            text_color="#64748B",
            anchor="w",
        )

        self.user_channels_title.grid(
            row=0,
            column=0,
            columnspan=2,
            padx=(5, 5),
            pady=(0, 2),
            sticky="w",
        )

        voice_title = self._get_localized_text(
            "matrix_voice",
            "VOICE",
        )

        self.voice_title = ctk.CTkLabel(
            self.controls_grid,
            text=voice_title,
            font=("Arial", 10, "bold"),
            text_color="#64748B",
            anchor="w",
        )

        self.voice_title.grid(
            row=0,
            column=2,
            padx=5,
            pady=(0, 2),
            sticky="w",
        )

        ai_channels_title = self._get_localized_text(
            "matrix_ai_channels",
            "AI CHANNELS",
        )

        self.ai_channels_title = ctk.CTkLabel(
            self.controls_grid,
            text=ai_channels_title,
            font=("Arial", 10, "bold"),
            text_color="#64748B",
            anchor="w",
        )

        self.ai_channels_title.grid(
            row=0,
            column=3,
            columnspan=2,
            padx=5,
            pady=(0, 2),
            sticky="w",
        )

        # ======================================================
        # USER / CHANNEL 1
        # ======================================================

        chat_switch_str = self._get_localized_text(
            "chat_user_switch",
            "Channel 1",
        )

        self.chat_switch = ctk.CTkSwitch(
            self.controls_grid,
            text=chat_switch_str,
            command=self.sync_matrix_to_core,
            font=("Arial", 12),
            text_color="#E2E8F0",
        )

        self.chat_switch.grid(
            row=1,
            column=0,
            padx=5,
            pady=(0, 2),
            sticky="w",
        )

        # ======================================================
        # USER / VOICE
        # ======================================================

        user_voice_label = self._get_localized_text(
            "voice_user_label",
            "Voice",
        )

        self.voice_user_switch = ctk.CTkSwitch(
            self.controls_grid,
            text=user_voice_label,
            command=self.on_user_voice_toggle,
            font=("Arial", 12),
            text_color="#E2E8F0",
        )

        self.voice_user_switch.grid(
            row=1,
            column=1,
            padx=5,
            pady=(0, 2),
            sticky="w",
        )

        # ======================================================
        # VOICE / MODE SELECTOR
        # ======================================================

        voice_mode_off_icon = self._get_localized_text(
            "icon_voice_mode_off",
            "VOICE_OFF",
        )

        voice_mode_ptt_icon = self._get_localized_text(
            "icon_voice_mode_ptt",
            "VOICE_PTT",
        )

        voice_mode_persistent_icon = self._get_localized_text(
            "icon_voice_mode_persistent",
            "VOICE_LISTEN",
        )

        voice_modes_list = [
            voice_mode_off_icon,
            voice_mode_ptt_icon,
            voice_mode_persistent_icon,
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
            row=1,
            column=2,
            padx=5,
            pady=(0, 2),
            sticky="ew",
        )

        self.voice_mode_btn.set(
            voice_modes_list[0]
        )

        def _update_voice_btn_color(mode):

            if mode == voice_modes_list[0]:
                self.voice_mode_btn.configure(
                    selected_color="#DC2626",
                    font=("Arial", 16),
                )

            elif mode == voice_modes_list[1]:
                self.voice_mode_btn.configure(
                    selected_color="#059669",
                    font=("Arial", 14),
                )

            elif mode == voice_modes_list[2]:
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

        # ======================================================
        # AI / VOICE
        # ======================================================

        ai_voice_label = self._get_localized_text(
            "voice_ai_label",
            "Voice",
        )

        self.voice_ai_switch = ctk.CTkSwitch(
            self.controls_grid,
            text=ai_voice_label,
            command=self.on_ai_voice_toggle,
            font=("Arial", 12),
            text_color="#E2E8F0",
        )

        self.voice_ai_switch.grid(
            row=1,
            column=3,
            padx=5,
            pady=(0, 2),
            sticky="w",
        )

        # ======================================================
        # AI / CHANNEL 1
        # ======================================================

        ai_chat_switch_str = self._get_localized_text(
            "chat_ai_switch",
            "Channel 1",
        )

        self.ai_chat_switch = ctk.CTkSwitch(
            self.controls_grid,
            text=ai_chat_switch_str,
            command=self.sync_matrix_to_core,
            font=("Arial", 12),
            text_color="#E2E8F0",
        )

        self.ai_chat_switch.grid(
            row=1,
            column=4,
            padx=5,
            pady=(0, 2),
            sticky="w",
        )

        # AI Channel 1 is enabled by default.
        self.ai_chat_switch.select()

        self.runtime_state.set_state(
            "ai_channel1_active",
            True
        )

        # ======================================================
        # ADAPTER / TELEMETRY
        # ======================================================

        tel_switch_str = self._get_localized_text(
            "telemetry_switch",
            "Read Telemetry",
        )

        self.read_telemetry_switch = ctk.CTkSwitch(
            self.controls_grid,
            text=tel_switch_str,
            command=self.on_telemetry_toggle,
            font=("Arial", 12),
            text_color="#E2E8F0",
        )

        self.read_telemetry_switch.grid(
            row=1,
            column=5,
            padx=5,
            pady=(0, 2),
            sticky="w",
        )

        self.read_telemetry_switch.deselect()

        self.read_telemetry_switch.configure(
            state="disabled"
        )

        # ======================================================
        # ADAPTER / CHANNEL 2
        # ======================================================

        write_switch_str = self._get_localized_text(
            "write_switch",
            "Write to Adapter",
        )

        self.write_adapter_switch = ctk.CTkSwitch(
            self.controls_grid,
            text=write_switch_str,
            command=self.sync_matrix_to_core,
            font=("Arial", 12),
            text_color="#E2E8F0",
        )

        self.write_adapter_switch.grid(
            row=1,
            column=6,
            padx=5,
            pady=(0, 2),
            sticky="w",
        )

        self.write_adapter_switch.configure(
            state="disabled"
        )

        # ======================================================
        # CHAT FRAME
        #
        # Fixed base layout:
        # ChatWindow = 960 x 540.
        # Chat frame = 980 x 560.
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

        # Restore persistent chat text color.
        saved_text_color = "#FFFFFF"

        if (
            self.core_hub
            and hasattr(
                self.core_hub,
                "global_config"
            )
        ):
            saved_text_color = self.core_hub.global_config.get(
                "chat_text_color",
                "#FFFFFF",
            )

        self.chat_window.set_text_color(
            saved_text_color
        )

        # ======================================================
        # CHAT SCROLLBAR
        # ======================================================

        self.chat_scrollbar = ctk.CTkScrollbar(
            self.main_container,
            orientation="vertical",
        )

        self.chat_scrollbar.grid(
            row=2,
            column=1,
            padx=(0, 10),
            pady=5,
            sticky="ns",
        )

        self._connect_chat_scrollbar()

        # ======================================================
        # BOTTOM INPUT
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

        placeholder_str = self._get_localized_text(
            "input_placeholder",
            "Type message...",
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

        send_str = self._get_localized_text(
            "send_btn",
            "Send",
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

        # ======================================================
        # TGBLOCK
        # ======================================================

        tgblock_unlocked_icon = self._get_localized_text(
            "icon_tgblock_unlocked",
            "TGBLOCK_UNLOCKED",
        )

        self.lock_icon_label = ctk.CTkLabel(
            self.control_frame,
            text=tgblock_unlocked_icon,
            font=("Arial", 16),
        )

        self.lock_icon_label.pack(
            side="right",
            padx=(5, 2),
        )

        self.lock_switch = ctk.CTkSwitch(
            self.control_frame,
            text="",
            command=self.on_lock_toggle,
            width=45,
        )

        self.lock_switch.pack(
            side="right",
            padx=(0, 15),
        )

        orig_lock_toggle = self.on_lock_toggle

        def _wrapped_lock_toggle():

            orig_lock_toggle()

            icon = (
                self._get_localized_text(
                    "icon_tgblock_locked",
                    "TGBLOCK_LOCKED",
                )
                if self.runtime_state.get_state("locked")
                else self._get_localized_text(
                    "icon_tgblock_unlocked",
                    "TGBLOCK_UNLOCKED",
                )
            )

            self.lock_icon_label.configure(
                text=icon
            )

        self.lock_switch.configure(
            command=_wrapped_lock_toggle
        )

        # ======================================================
        # LEFT-SIDE CONTROL BAR
        # ======================================================

        topmost_str = self._get_localized_text(
            "topmost_toggle",
            "Stay on Top",
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

        text_size_icon = self._get_localized_text(
            "icon_text_size",
            "TEXT_SIZE",
        )

        text_size_label = self._get_localized_text(
            "text_size_label",
            "Text Size",
        )

        self.text_size_switch = ctk.CTkSwitch(
            self.control_frame,
            text=f"{text_size_icon} {text_size_label}",
            command=self.on_text_size_toggle,
        )

        self.text_size_switch.pack(
            side="left",
            padx=10,
        )

        text_color_icon = self._get_localized_text(
            "icon_text_color",
            "🎨",
        )

        text_color_label = self._get_localized_text(
            "text_color_label",
            "Text Color",
        )

        self.text_color_btn = ctk.CTkButton(
            self.control_frame,
            text=f"{text_color_icon} {text_color_label}",
            command=self.open_text_color_picker,
            width=110,
        )

        self.text_color_btn.pack(
            side="left",
            padx=10,
        )

        monitor_icon = self._get_localized_text(
            "icon_monitor",
            "MONITOR",
        )

        monitor_label = self._get_localized_text(
            "monitor_label",
            "Monitor",
        )

        self.monitor_switch = ctk.CTkSwitch(
            self.control_frame,
            text=f"{monitor_icon} {monitor_label}",
            command=self.toggle_monitor_panel,
        )

        self.monitor_switch.pack(
            side="left",
            padx=10,
        )

        # ======================================================
        # SETTINGS
        # ======================================================

        settings_str = self._get_localized_text(
            "settings_btn",
            "Settings",
        )

        self.settings_btn = ctk.CTkButton(
            self.control_frame,
            text=settings_str,
            command=self.on_settings_open,
            width=80,
        )

        self.settings_btn.pack(
            side="left",
            padx=5,
        )

        # ======================================================
        # PTT HOTKEY
        # ======================================================

        ptt_hotkey_icon = self._get_localized_text(
            "icon_ptt_hotkey",
            "PTT_HOTKEY",
        )

        self.hotkey_btn = ctk.CTkButton(
            self.control_frame,
            text=ptt_hotkey_icon,
            command=self.start_hotkey_capture,
            width=65,
            font=("Arial", 16, "bold"),
            fg_color="#374151",
            hover_color="#4B5563",
        )

        self.hotkey_btn.pack(
            side="left",
            padx=5,
        )

        # ======================================================
        # RESET
        # ======================================================

        reset_str = self._get_localized_text(
            "reset_btn",
            "Reset",
        )

        self.reset_btn = ctk.CTkButton(
            self.control_frame,
            text=reset_str,
            command=lambda: None,
            width=70,
            fg_color="#DC2626",
            hover_color="#EF4444",
        )

        self.reset_btn.pack(
            side="left",
            padx=5,
        )

        # ======================================================
        # FIXED INITIAL GEOMETRY
        # ======================================================

        self.update_idletasks()

        fixed_window_width = 1026
        fixed_window_height = 815

        self.minsize(
            fixed_window_width,
            fixed_window_height,
        )

        self.maxsize(
            fixed_window_width,
            fixed_window_height,
        )

        self.geometry(
            f"{fixed_window_width}x"
            f"{fixed_window_height}"
        )

        self.update_idletasks()

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
            "| locked=",
            fixed_window_width,
            "x",
            fixed_window_height,
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