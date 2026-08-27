# -*- coding: utf-8 -*-
"""
CONNECTIONS:
- FETCHES FROM: interface/audio_io.py, interface/hardware_io.py, 
  core/localization_core.py
- CALLED BY: corefuntions/bridge_functions.py, main/main.py
"""
import threading
import time

class VoiceCore:
    def __init__(self, audio_subsystem, hardware_subsystem):
        self.audio = audio_subsystem
        self.hardware = hardware_subsystem
        self.is_recording = False
        self._loop_active = False

    def execute_ptt_transaction(self, target_key, running_check_callback, 
                               success_callback, current_mode_callback):
        """Asynchronously orchestrates a clean voice interaction cycle supporting 
        both PTT and iterative LISTEN loops."""
        if self.is_recording:
            return
        self.is_recording = True

        def worker():
            try:
                # FIXED: Shifted from dangerous recursive calling to a flat, safe iterative while-loop
                while running_check_callback():
                    active_mode = str(current_mode_callback()).upper()

                    # Context A: If Push-To-Talk, launch the hardware block until the physical key is released
                    if active_mode == "PTT":
                        release_thread = threading.Thread(
                            target=self.hardware.block_until_release, 
                            args=(target_key, running_check_callback), 
                            daemon=True
                        )
                        release_thread.start()

                    # Open the audio hardware vector and capture human speech tokens
                    captured_text = ""
                    if self.audio:
                        captured_text = self.audio.listen()

                    # Synchronize and ensure the hotkey is released if we were in PTT mode
                    if active_mode == "PTT":
                        while not self.hardware.key_released_event and running_check_callback():
                            # SÄKERHETSSPÄRR: Om läget ändras i GUI under pågående väntan, bryt omedelbart
                            if str(current_mode_callback()).upper() != "PTT":
                                break
                            time.sleep(0.02)

                    # Dispatch the finalized tokens transactionally to the core bridge pipeline
                    if captured_text and captured_text.strip():
                        success_callback(captured_text)

                    # Context B: Continuous Iterative Listen Loop Check
                    # Supports both English (LISTEN) and Swedish (LYSSNA) localized tokens cleanly
                    if active_mode in ["LISTEN", "LYSSNA"] and running_check_callback():
                        time.sleep(0.3) # Give the soundcard hardware buffer a brief moment to settle
                        continue # Iterate cleanly on the same thread without stack leakage
                    else:
                        break # Terminate worker thread execution if mode has changed

            except Exception as e:
                print(f"[VOICE-CORE-ERROR] Asynchronous voice transaction failed: {e}")
            finally:
                self.is_recording = False

        threading.Thread(target=worker, daemon=True).start()
