# -*- coding: utf-8 -*-
"""
CONNECTIONS:
  - FETCHES FROM: No internal logic files (External hardware binding layer).
  - CALLED BY: core/bridge_core.py
"""

import pyttsx3
import speech_recognition as sr

class AudioIO:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Adjusted pause threshold to resolve human vocal patterns faster
        self.recognizer.pause_threshold = 1.0 

    def speak(self, text: str):
        """Asynchronously initializes the local TTS engine to output vocal tokens."""
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 160)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[AUDIO-ERROR] Text-to-speech engine execution failed: {e}")

    def listen(self) -> str:
        """Opens the hardware audio vector, capturing speech data safely without rigid blocking timeouts."""
        try:
            with sr.Microphone() as source:
                print("[SYSTEM] Audio intercept active (Channel 1 stream). Awaiting speech...")
                # Dynamically sample ambient background noise before capturing tokens
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                
                # Dynamic capture: Removed the hard timeout barrier that caused thread blocking crashes
                audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=8.0)
                
            # Enforces native Swedish token interpretation for core interaction flows
            return self.recognizer.recognize_google(audio, language="sv-SE")
        except Exception as e:
            print(f"[AUDIO-DEBUG] Audio capture transaction details: {e}")
            return ""

