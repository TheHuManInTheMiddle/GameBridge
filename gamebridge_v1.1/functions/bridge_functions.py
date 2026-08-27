# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
 - HÄMTAR FRÅN: interface/audio_io.py, adapters/adapter_loader.py,
   ai/ollama_client.py, core/channel_matrix.py, interface/hardware_io.py,
   core/path_core.py, core/config_core.py, core/hotkey_capture_core.py,
   core/cognitive_router_core.py
 - ANROPAS AV: main/main.py, interface/client_gui.py
"""
import threading
import time
import os
import json
import sys
import keyboard
from interface.audio_io import AudioIO
from adapters.adapter_loader import AdapterLoader
from ai.ollama_client import OllamaClient
from interface.hardware_io import HardwareIO
from core.path_core import PathCore
from core.config_core import ConfigCore
from core.hotkey_capture_core import HotkeyCaptureCore
from core.cognitive_router_core import CognitiveRouterCore


# =========================================================================
# 1. PROCEDURFUNKTIONER (UTBRUTNA ENLIGT FAS C)
# =========================================================================

def function_play_welcome_message(audio_instance, gui_instance, current_voice_hotkey):
    """Asynchronously dispatches the audio confirmation chime and log events."""
    time.sleep(0.5)

    if sys.platform == "win32":
        import ctypes
        try:
            ctypes.windll.ole32.CoInitialize(None)
        except Exception:
            pass

    audio_instance.speak("System online.")

    if gui_instance:
        gui_instance.append_log(
            "SYSTEM",
            f"G.A.M.E. B.R.I.D.G.E. operational. "
            f"Baseline voice hotkey resolved to [{current_voice_hotkey.upper()}]."
        )

    if sys.platform == "win32":
        try:
            ctypes.windll.ole32.CoUninitialize()
        except Exception:
            pass


def function_setup_hardware_hotkeys(core_instance):
    """Thread worker loop supervising keyboard input and triggering voice modes."""
    error_count = 0

    while core_instance.running:
        if core_instance.gui and hasattr(core_instance.gui, "voice_mode_btn"):
            current_mode = core_instance.gui.voice_mode_btn.get()

            # GUI-presentation -> internal voice-mode contract.
            # The GUI uses icons; the voice/core layer uses stable semantic values.
            voice_mode_map = {
                "  🔇 ": "OFF",
                "🔘🎙️": "PTT",
                "  🎙️ ": "LISTEN",
                "OFF": "OFF",
                "AV": "OFF",
                "off": "OFF",
                "av": "OFF",
                "PTT": "PTT",
                "LISTEN": "LISTEN",
                "LYSSNA": "LISTEN",
            }

            normalized_mode = voice_mode_map.get(current_mode, current_mode)
            normalized_mode = str(normalized_mode).upper()

            if normalized_mode != "OFF":
                raw_target_key = core_instance.current_voice_hotkey

                try:
                    # Normalize the configured hotkey through HardwareIO.
                    normalized_key = core_instance.hardware.normalize_key(raw_target_key)

                    is_listen_mode = normalized_mode == "LISTEN"

                    # LISTEN starts automatically.
                    # PTT starts only while the configured hotkey is held.
                    if (
                        (is_listen_mode or keyboard.is_pressed(normalized_key))
                        and core_instance.voice
                        and not core_instance.voice.is_recording
                    ):
                        core_instance.voice.execute_ptt_transaction(
                            target_key=normalized_key,
                            running_check_callback=lambda: core_instance.running,
                            success_callback=core_instance.on_voice_token_resolved,
                            current_mode_callback=lambda: voice_mode_map.get(
                                core_instance.gui.voice_mode_btn.get(),
                                core_instance.gui.voice_mode_btn.get()
                            )
                        )

                    error_count = 0

                except Exception as e:
                    error_count += 1

                    if error_count <= 5:
                        print(f"[CORE-ERROR] Keyboard state scan faulted: {e}")
                    elif error_count == 6:
                        print(
                            "[CORE-WARNING] Keyboard errors repeating rapidly. "
                            "Silencing terminal output to protect performance."
                        )

        time.sleep(0.05)


# =========================================================================
# 2. HUVUDKLASS (TILLSTÅNDSDIRIGENT)
# =========================================================================

class GameBridgeCore:
    def __init__(self):
        self.gui = None
        self.audio = AudioIO()
        self.hardware = HardwareIO()
        self.matrix = None
        self.voice = None
        self.io_layer = None
        self.localizer = None
        self.telemetry_worker = None

        self.config_manager = ConfigCore()
        self.hotkey_capturer = HotkeyCaptureCore(self.hardware)
        self.cognitive_router = None

        self.active_adapter_instance = None
        self.current_adapter_folder = "None"

        self.is_listening = False
        self.running = True

        # EXPANSION v3.0: Användarkontrollerad capability för Internet AI
        self.internet_ai_enabled = False

        self.global_config = self.config_manager.load_global_config()
        self.config_path = self.config_manager.config_path

        self.current_voice_hotkey = self.global_config.get(
            "voice_hotkey",
            "f12"
        ).lower()

        self.ai_client = OllamaClient(
            model_name=self.global_config.get(
                "ai_model_name",
                "None"
            )
        )

        try:
            self.loader = AdapterLoader(
                plugin_dir=PathCore.get_adapter_root()
            )
            self.available_adapters = self.loader.discover_and_load()
        except Exception as e:
            print(
                f"[CORE-ERROR] Dynamic extension discovery failed: {e}"
            )
            self.available_adapters = {}

    def link_gui(self, gui_instance):
        """Cross-references the presentation layer boundaries transactionally."""
        self.gui = gui_instance

        self.cognitive_router = CognitiveRouterCore(
            ai_client=self.ai_client,
            matrix=self.matrix,
            io_layer=self.io_layer,
            core_parent=self
        )

        is_eng = (
            hasattr(self.gui, "system_lang")
            and self.gui.system_lang == "en"
        )

        fallback_text = (
            "No Adapter Loaded"
            if is_eng
            else "Ingen Adapter Laddad"
        )

        adapter_list = [fallback_text]

        if self.available_adapters:
            adapter_list.extend(
                list(self.available_adapters.keys())
            )

        if self.gui and hasattr(self.gui, "adapter_selector"):
            self.gui.adapter_selector.configure(
                values=adapter_list
            )
            self.gui.adapter_selector.set(fallback_text)

        if self.gui and hasattr(self.gui, "internet_toggle"):
            initial_state = (
                "ON"
                if self.internet_ai_enabled
                else "OFF"
            )
            self.gui.internet_toggle.set(initial_state)

        if self.telemetry_worker:
            self.telemetry_worker.start_polling_worker(
                current_adapter_callback=lambda:
                    self.active_adapter_instance,
                success_ui_callback=lambda data:
                    self.gui.append_log(
                        "TELEMETRY",
                        str(data)
                    )
                    if self.gui
                    else print(data)
            )

    def update_internet_capability(self, enabled: bool):
        """Transactional setter invoked by UI event queue to flip internet capability state."""
        self.internet_ai_enabled = enabled

        log_msg = (
            "Internet AI capability activated (Port 8080 route armed)."
            if enabled
            else
            "Internet AI capability deactivated "
            "(Offline/Local enforcement active)."
        )

        if self.gui:
            self.gui.append_log("SYSTEM", log_msg)

    def boot_platform_loops(self):
        """Unified entry point invoking isolated background executions."""
        threading.Thread(
            target=function_setup_hardware_hotkeys,
            args=(self,),
            daemon=True
        ).start()

        threading.Thread(
            target=function_play_welcome_message,
            args=(
                self.audio,
                self.gui,
                self.current_voice_hotkey
            ),
            daemon=True
        ).start()

    def load_adapter_specific_hotkey(self):
        """Reflectively extracts runtime subdirectory names and dynamically binds hotkeys."""
        if not self.active_adapter_instance:
            self.current_adapter_folder = "None"
            self.global_config = (
                self.config_manager.load_global_config()
            )

            self.current_voice_hotkey = self.global_config.get(
                "voice_hotkey",
                "f12"
            ).lower()

            return

        module_name = (
            self.active_adapter_instance.__class__.__module__
        )

        parts = module_name.split(".")

        if len(parts) >= 1:
            self.current_adapter_folder = parts[0]
        else:
            self.current_adapter_folder = "None"

        config_file = PathCore.get_adapter_file(
            self.current_adapter_folder,
            "plugin_config.json"
        )

        if os.path.exists(config_file):
            try:
                with open(
                    config_file,
                    "r",
                    encoding="utf-8"
                ) as f:
                    plugin_data = json.load(f)

                self.current_voice_hotkey = plugin_data.get(
                    "voice_hotkey",
                    self.global_config.get(
                        "voice_hotkey",
                        "f12"
                    )
                ).lower()

                print(
                    f"[CORE] Dynamic hotkey hot-swap execution: "
                    f"[{self.current_voice_hotkey.upper()}] "
                    f"bended to {self.current_adapter_folder}"
                )

                return

            except Exception:
                pass

        self.current_voice_hotkey = self.global_config.get(
            "voice_hotkey",
            "f12"
        ).lower()

    def handle_adapter_switch(self, adapter_name: str):
        """Safely hot-swaps active adapter interfaces on the execution stack."""
        if adapter_name in self.available_adapters:
            if self.active_adapter_instance:
                self.active_adapter_instance.shutdown()

            adapter_class = self.available_adapters[adapter_name]
            self.active_adapter_instance = adapter_class()
            self.active_adapter_instance.initialize()

            if self.io_layer:
                self.io_layer.register_adapter_channels(
                    input_cb=self.active_adapter_instance.execute_interaction,
                    output_cb=self.active_adapter_instance.read_telemetry
                )

            self.load_adapter_specific_hotkey()

            if self.gui:
                self.gui.append_log(
                    "SYSTEM",
                    f"Extension stack mutated. "
                    f"Allocated runtime focus to '{adapter_name}'."
                )

    def unload_active_adapter(self):
        """Detaches active extension frameworks, reverting state boundaries."""
        if self.active_adapter_instance:
            self.active_adapter_instance.shutdown()

        self.active_adapter_instance = None
        self.current_adapter_folder = "None"

        self.global_config = (
            self.config_manager.load_global_config()
        )

        self.current_voice_hotkey = self.global_config.get(
            "voice_hotkey",
            "f12"
        ).lower()

    def boot_target_application(self):
        """Asynchronously executes target app boot processes via adapter hooks."""
        if self.active_adapter_instance:
            threading.Thread(
                target=self.active_adapter_instance.boot_or_attach,
                daemon=True
            ).start()
        else:
            if self.gui:
                self.gui.append_log(
                    "SYSTEM-WARNING",
                    "Execution request denied: "
                    "No target extension currently deployed."
                )

    def set_channels_state(self, k1: bool, k2: bool):
        """Enforces routing authorization flags for internal cross-transference."""
        if self.matrix:
            self.matrix.update_states(
                k1,
                k2,
                self.matrix.ai_generation_enabled,
                self.matrix.internet_ai_enabled
            )

    def capture_new_hotkey(self):
        """Leverages the decoupled HotkeyCaptureCore to intercept raw peripheral events safely."""
        if not self.gui or not self.hotkey_capturer:
            return

        def _before():
            pass

        def _success(cleaned_key: str):
            self.current_voice_hotkey = cleaned_key

            if (
                self.active_adapter_instance
                and self.current_adapter_folder != "None"
            ):
                self.config_manager.save_adapter_hotkey(
                    self.current_adapter_folder,
                    cleaned_key
                )

                self.gui.append_log(
                    "SYSTEM",
                    f"Dynamic hotkey persisted to target "
                    f"extension workspace: [{cleaned_key.upper()}]"
                )
            else:
                self.global_config["voice_hotkey"] = cleaned_key

                self.config_manager.save_global_config(
                    self.global_config
                )

                self.gui.append_log(
                    "SYSTEM",
                    f"Dynamic hotkey persisted to global engine "
                    f"configuration: [{cleaned_key.upper()}]"
                )

        def _final():
            is_eng = (
                getattr(self.gui, "system_lang", "en")
                == "en"
            )

            self.gui.status_label.configure(
                text="Status: Ready"
                if is_eng
                else "Status: Redo"
            )

            if hasattr(self.gui, "hotkey_btn"):
                self.gui.hotkey_btn.configure(
                    fg_color="#374151"
                )

        self.hotkey_capturer.capture_next_keypress(
            _before,
            _success,
            _final
        )

    def on_voice_token_resolved(self, recognized_text: str):
        """Callback executed transactionally by VoiceCore when clean text tokens are decoded."""
        if self.gui:
            sender_tag = (
                "USER (Channel 1)"
                if getattr(self.gui, "system_lang", "en") == "en"
                else "ANVÄNDARE (Kanal 1)"
            )

            self.gui.append_log(
                sender_tag,
                recognized_text
            )

        self.process_chatt_flow(recognized_text)

    def process_chatt_flow(self, user_text: str):
        """Relays cognitive token tracking safely through the decoupled router core sub-system."""
        if not self.cognitive_router:
            return

        def _ui_status(state: str):
            if self.gui:
                is_eng = (
                    getattr(self.gui, "system_lang", "en")
                    == "en"
                )

                if state == "PROCESSING":
                    self.gui.status_label.configure(
                        text=(
                            "Status: Processing..."
                            if is_eng
                            else "Status: Processar..."
                        )
                    )
                else:
                    self.gui.status_label.configure(
                        text=(
                            "Status: Ready"
                            if is_eng
                            else "Status: Redo"
                        )
                    )

        def _gui_log(sender: str, text: str):
            if self.gui:
                self.gui.append_log(sender, text)

        def _speech(text_to_speak: str):
            if self.gui and hasattr(
                self.gui,
                "voice_mode_btn"
            ):
                current_mode = self.gui.voice_mode_btn.get()

                voice_mode_map = {
                    "  🔇 ": "OFF",
                    "🔘🎙️": "PTT",
                    "  🎙️ ": "LISTEN",
                    "OFF": "OFF",
                    "AV": "OFF",
                    "off": "OFF",
                    "av": "OFF",
                    "PTT": "PTT",
                    "LISTEN": "LISTEN",
                    "LYSSNA": "LISTEN",
                }

                normalized_mode = voice_mode_map.get(
                    current_mode,
                    current_mode
                )

                if str(normalized_mode).upper() != "OFF":
                    if hasattr(self, "audio") and self.audio:
                        threading.Thread(
                            target=self.audio.speak,
                            args=(text_to_speak,),
                            daemon=True
                        ).start()

        self.cognitive_router.route_transactional_flow(
            user_text=user_text,
            active_adapter=self.active_adapter_instance,
            adapter_folder=self.current_adapter_folder,
            gui_log_callback=_gui_log,
            ui_status_callback=_ui_status,
            speech_callback=_speech
        )