# interface/settings_window.py

# -*- coding: utf-8 -*-

import customtkinter as ctk

from core.settings_providers import (
    get_supported_languages,
    get_ai_providers,
    get_internet_providers,
    get_tts_providers,
    get_available_voices,
)


class SettingsWindow(ctk.CTkToplevel):

    def __init__(
        self,
        parent,
        core_hub=None,
        localizer=None,
        runtime_state=None,
    ):
        super().__init__(parent)

        self.parent = parent
        self.core_hub = core_hub
        self.localizer = localizer
        self.runtime_state = runtime_state

        self._tts_voice_map = {}

        self.title("Settings")
        self.resizable(False, False)
        self.transient(parent)

        self._build_ui()

        self.update_idletasks()

        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        window_width = self.winfo_reqwidth()
        window_height = self.winfo_reqheight()

        x = (
            parent_x
            + (parent_width - window_width) // 2
        )

        y = (
            parent_y
            + (parent_height - window_height) // 2
        )

        self.geometry(
            f"{window_width}x"
            f"{window_height}+{x}+{y}"
        )

        self.focus_force()

    # ==========================================================
    # CONFIGURATION
    # ==========================================================

    def _save_global_setting(self, key, value):
        """Updates the active global configuration and persists it."""

        if not self.core_hub:
            return

        self.core_hub.global_config[key] = value

        if hasattr(
            self.core_hub,
            "config_manager"
        ):
            self.core_hub.config_manager.save_global_config(
                self.core_hub.global_config
            )

    def _on_language_change(self, selected_language):
        """Persists the selected system language for the next startup."""

        self._save_global_setting(
            "system_language",
            selected_language
        )

    def _on_ai_provider_change(self, selected_provider):
        """Updates, persists and applies the active AI provider."""

        self._save_global_setting(
            "ai_provider",
            selected_provider
        )

        if self.parent and hasattr(
            self.parent,
            "refresh_ai_provider"
        ):
            self.parent.refresh_ai_provider(
                selected_provider
            )

    def _on_internet_provider_change(self, selected_provider):
        """Updates and persists the active Internet provider."""

        self._save_global_setting(
            "internet_provider",
            selected_provider
        )

    def _build_tts_voice_list(self, voices):
        """Build voice presentation values and map them to real IDs."""

        voice_values = []
        self._tts_voice_map = {}

        for voice in voices:
            if isinstance(voice, dict):
                voice_name = voice.get("name")
                voice_id = voice.get("id")

                if voice_name and voice_id:
                    voice_name = str(voice_name)
                    voice_id = str(voice_id)

                    voice_values.append(
                        voice_name
                    )

                    self._tts_voice_map[
                        voice_name
                    ] = voice_id

            elif voice:
                voice_name = str(voice)

                voice_values.append(
                    voice_name
                )

                self._tts_voice_map[
                    voice_name
                ] = voice_name

        if not voice_values:
            voice_values = ["none"]

        return voice_values

    def _get_voice_display_name(self, voice_id):
        """Return the presentation name for a stored voice ID."""

        if not voice_id:
            return None

        for display_name, mapped_id in self._tts_voice_map.items():
            if mapped_id == voice_id:
                return display_name

        return None

    def _on_tts_provider_change(self, selected_provider):
        """Updates the active TTS provider and refreshes available voices."""

        self._save_global_setting(
            "tts_provider",
            selected_provider
        )

        voices = get_available_voices(
            selected_provider
        )

        voice_values = self._build_tts_voice_list(
            voices
        )

        self.voice_selector.configure(
            values=voice_values
        )

        current_voice_id = "none"

        if self.core_hub:
            current_voice_id = (
                self.core_hub.global_config.get(
                    "tts_voice",
                    "none"
                )
            )

        current_display_name = (
            self._get_voice_display_name(
                current_voice_id
            )
        )

        if current_display_name:
            self.voice_selector.set(
                current_display_name
            )
        else:
            selected_display_name = voice_values[0]

            self.voice_selector.set(
                selected_display_name
            )

            selected_voice_id = (
                self._tts_voice_map.get(
                    selected_display_name,
                    selected_display_name
                )
            )

            self._save_global_setting(
                "tts_voice",
                selected_voice_id
            )

    def _on_tts_voice_change(self, selected_voice):
        """Persists the real TTS voice ID for the selected voice."""

        voice_id = self._tts_voice_map.get(
            selected_voice,
            selected_voice
        )

        self._save_global_setting(
            "tts_voice",
            voice_id
        )

    # ==========================================================
    # MONITOR SETTINGS
    # ==========================================================

    def _on_channel2_monitor_toggle(self):
        """Persists Channel 2 monitor presentation state."""

        self._save_global_setting(
            "channel2_monitor_active",
            bool(self.channel2_monitor_switch.get())
        )

    def _on_telemetry_monitor_toggle(self):
        """Persists Telemetry monitor presentation state."""

        self._save_global_setting(
            "telemetry_monitor_active",
            bool(self.telemetry_monitor_switch.get())
        )

    # ==========================================================
    # BUILD UI
    # ==========================================================

    def _build_ui(self):

        frame = ctk.CTkFrame(
            self,
            corner_radius=10,
        )

        frame.pack(
            padx=10,
            pady=10,
            fill="both",
            expand=True,
        )

        # ------------------------------------------------------
        # LANGUAGE
        # ------------------------------------------------------

        ctk.CTkLabel(
            frame,
            text="Language",
            font=("Arial", 12, "bold"),
        ).grid(
            row=0,
            column=0,
            padx=(15, 10),
            pady=(15, 8),
            sticky="w",
        )

        language_values = get_supported_languages()

        if not language_values:
            language_values = ["en"]

        self.language_selector = ctk.CTkOptionMenu(
            frame,
            values=language_values,
            width=180,
            command=self._on_language_change,
        )

        self.language_selector.grid(
            row=0,
            column=1,
            padx=(10, 15),
            pady=(15, 8),
        )

        current_language = "en"

        if self.core_hub:
            current_language = self.core_hub.global_config.get(
                "system_language",
                "en"
            )

        if current_language in language_values:
            self.language_selector.set(
                current_language
            )
        else:
            self.language_selector.set(
                language_values[0]
            )

        # ------------------------------------------------------
        # AI PROVIDER
        # ------------------------------------------------------

        ctk.CTkLabel(
            frame,
            text="AI Provider",
            font=("Arial", 12, "bold"),
        ).grid(
            row=1,
            column=0,
            padx=(15, 10),
            pady=8,
            sticky="w",
        )

        ai_provider_values = get_ai_providers()

        if not ai_provider_values:
            ai_provider_values = []

        if "none" in ai_provider_values:
            ai_provider_values = [
                "none"
            ] + [
                provider
                for provider in ai_provider_values
                if provider != "none"
            ]
        else:
            ai_provider_values = [
                "none"
            ] + ai_provider_values

        self.ai_provider_selector = ctk.CTkOptionMenu(
            frame,
            values=ai_provider_values,
            width=180,
            command=self._on_ai_provider_change,
        )

        self.ai_provider_selector.grid(
            row=1,
            column=1,
            padx=(10, 15),
            pady=8,
        )

        current_ai_provider = "none"

        if self.core_hub:
            current_ai_provider = (
                self.core_hub.global_config.get(
                    "ai_provider",
                    "none"
                )
            )

        if current_ai_provider in ai_provider_values:
            self.ai_provider_selector.set(
                current_ai_provider
            )
        else:
            self.ai_provider_selector.set(
                ai_provider_values[0]
            )

            self._save_global_setting(
                "ai_provider",
                ai_provider_values[0]
            )

        # ------------------------------------------------------
        # INTERNET PROVIDER
        # ------------------------------------------------------

        ctk.CTkLabel(
            frame,
            text="Internet Provider",
            font=("Arial", 12, "bold"),
        ).grid(
            row=2,
            column=0,
            padx=(15, 10),
            pady=8,
            sticky="w",
        )

        internet_provider_values = get_internet_providers()

        if not internet_provider_values:
            internet_provider_values = []

        if "none" in internet_provider_values:
            internet_provider_values = [
                "none"
            ] + [
                provider
                for provider in internet_provider_values
                if provider != "none"
            ]
        else:
            internet_provider_values = [
                "none"
            ] + internet_provider_values

        self.internet_provider_selector = ctk.CTkOptionMenu(
            frame,
            values=internet_provider_values,
            width=180,
            command=self._on_internet_provider_change,
        )

        self.internet_provider_selector.grid(
            row=2,
            column=1,
            padx=(10, 15),
            pady=8,
        )

        current_internet_provider = "none"

        if self.core_hub:
            current_internet_provider = (
                self.core_hub.global_config.get(
                    "internet_provider",
                    "none"
                )
            )

        if current_internet_provider in internet_provider_values:
            self.internet_provider_selector.set(
                current_internet_provider
            )
        else:
            self.internet_provider_selector.set(
                internet_provider_values[0]
            )

        # ------------------------------------------------------
        # TTS PROVIDER
        # ------------------------------------------------------

        ctk.CTkLabel(
            frame,
            text="TTS Provider",
            font=("Arial", 12, "bold"),
        ).grid(
            row=3,
            column=0,
            padx=(15, 10),
            pady=8,
            sticky="w",
        )

        tts_provider_values = get_tts_providers()

        if not tts_provider_values:
            tts_provider_values = []

        if "none" in tts_provider_values:
            tts_provider_values = [
                "none"
            ] + [
                provider
                for provider in tts_provider_values
                if provider != "none"
            ]
        else:
            tts_provider_values = [
                "none"
            ] + tts_provider_values

        self.tts_provider_selector = ctk.CTkOptionMenu(
            frame,
            values=tts_provider_values,
            width=180,
            command=self._on_tts_provider_change,
        )

        self.tts_provider_selector.grid(
            row=3,
            column=1,
            padx=(10, 15),
            pady=8,
        )

        current_tts_provider = "none"

        if self.core_hub:
            current_tts_provider = (
                self.core_hub.global_config.get(
                    "tts_provider",
                    "none"
                )
            )

        if current_tts_provider in tts_provider_values:
            self.tts_provider_selector.set(
                current_tts_provider
            )
        else:
            self.tts_provider_selector.set(
                tts_provider_values[0]
            )

        # ------------------------------------------------------
        # VOICE
        # ------------------------------------------------------

        ctk.CTkLabel(
            frame,
            text="Voice",
            font=("Arial", 12, "bold"),
        ).grid(
            row=4,
            column=0,
            padx=(15, 10),
            pady=8,
            sticky="w",
        )

        initial_voices = get_available_voices(
            current_tts_provider
        )

        voice_values = self._build_tts_voice_list(
            initial_voices
        )

        self.voice_selector = ctk.CTkOptionMenu(
            frame,
            values=voice_values,
            width=180,
            command=self._on_tts_voice_change,
        )

        self.voice_selector.grid(
            row=4,
            column=1,
            padx=(10, 15),
            pady=8,
        )

        current_tts_voice = "none"

        if self.core_hub:
            current_tts_voice = (
                self.core_hub.global_config.get(
                    "tts_voice",
                    "none"
                )
            )

        current_display_name = (
            self._get_voice_display_name(
                current_tts_voice
            )
        )

        if current_display_name:
            self.voice_selector.set(
                current_display_name
            )
        else:
            self.voice_selector.set(
                voice_values[0]
            )

        # ------------------------------------------------------
        # CHANNEL 2 MONITOR
        # ------------------------------------------------------

        channel2_monitor_label = "Channel 2"

        if self.localizer:
            channel2_monitor_label = (
                self.localizer.get_text(
                    "channel2_monitor_switch"
                )
            )

        ctk.CTkLabel(
            frame,
            text=channel2_monitor_label,
            font=("Arial", 12, "bold"),
        ).grid(
            row=5,
            column=0,
            padx=(15, 10),
            pady=8,
            sticky="w",
        )

        self.channel2_monitor_switch = ctk.CTkSwitch(
            frame,
            text="",
            command=self._on_channel2_monitor_toggle,
        )

        self.channel2_monitor_switch.grid(
            row=5,
            column=1,
            padx=(10, 15),
            pady=8,
            sticky="w",
        )

        current_channel2_monitor = False

        if self.core_hub:
            current_channel2_monitor = (
                self.core_hub.global_config.get(
                    "channel2_monitor_active",
                    False
                )
            )

        if current_channel2_monitor:
            self.channel2_monitor_switch.select()
        else:
            self.channel2_monitor_switch.deselect()

        # ------------------------------------------------------
        # TELEMETRY MONITOR
        # ------------------------------------------------------

        telemetry_monitor_label = "Telemetry"

        if self.localizer:
            telemetry_monitor_label = (
                self.localizer.get_text(
                    "telemetry_monitor_switch"
                )
            )

        ctk.CTkLabel(
            frame,
            text=telemetry_monitor_label,
            font=("Arial", 12, "bold"),
        ).grid(
            row=6,
            column=0,
            padx=(15, 10),
            pady=8,
            sticky="w",
        )

        self.telemetry_monitor_switch = ctk.CTkSwitch(
            frame,
            text="",
            command=self._on_telemetry_monitor_toggle,
        )

        self.telemetry_monitor_switch.grid(
            row=6,
            column=1,
            padx=(10, 15),
            pady=8,
            sticky="w",
        )

        current_telemetry_monitor = False

        if self.core_hub:
            current_telemetry_monitor = (
                self.core_hub.global_config.get(
                    "telemetry_monitor_active",
                    False
                )
            )

        if current_telemetry_monitor:
            self.telemetry_monitor_switch.select()
        else:
            self.telemetry_monitor_switch.deselect()

        # ------------------------------------------------------
        # CLOSE
        # ------------------------------------------------------

        close_label = "Close"

        if self.localizer:
            close_label = self.localizer.get_text(
                "close_btn"
            )

        self.close_button = ctk.CTkButton(
            frame,
            text=close_label,
            command=self.destroy,
            width=100,
        )

        self.close_button.grid(
            row=7,
            column=0,
            columnspan=2,
            padx=15,
            pady=(15, 15),
        )