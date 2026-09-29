# -*- coding: utf-8 -*-
"""
CONNECTIONS:
  - FETCHES FROM: Global runtime configuration and TTS providers.
  - CALLED BY: functions/bridge_functions.py
"""

import importlib

import pyttsx3
import speech_recognition as sr


class AudioIO:
    def __init__(self, global_config=None):
        self.global_config = global_config or {}

        self.recognizer = sr.Recognizer()
        # Adjusted pause threshold to resolve human vocal patterns faster
        self.recognizer.pause_threshold = 1.0

    def _get_tts_provider(self):
        """Loads the configured TTS provider dynamically."""

        provider_name = self.global_config.get(
            "tts_provider",
            "none"
        )

        if not provider_name or provider_name == "none":
            return None

        try:
            module_name = (
                f"providers.{provider_name}_tts"
            )

            return importlib.import_module(
                module_name
            )

        except Exception as e:
            print(
                "[AUDIO-ERROR] "
                f"Failed to load TTS provider "
                f"'{provider_name}': {e}"
            )
            return None

    def speak(self, text: str):
        """Outputs text using the configured TTS provider and voice."""

        try:
            provider = self._get_tts_provider()

            if provider is None:
                return

            voice_id = self.global_config.get(
                "tts_voice",
                "none"
            )

            engine = pyttsx3.init()
            engine.setProperty(
                "rate",
                160
            )

            if voice_id and voice_id != "none":
                engine.setProperty(
                    "voice",
                    voice_id
                )

            engine.say(text)
            engine.runAndWait()

        except Exception as e:
            print(
                "[AUDIO-ERROR] "
                f"Text-to-speech engine execution failed: {e}"
            )

    def listen(self) -> str:
        """Opens the hardware audio vector, capturing speech data safely without rigid blocking timeouts."""
        try:
            with sr.Microphone() as source:
                print(
                    "[SYSTEM] Audio intercept active "
                    "(Channel 1 stream). Awaiting speech..."
                )

                # Dynamically sample ambient background noise
                # before capturing tokens
                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.3
                )

                # Dynamic capture: Removed the hard timeout barrier
                # that caused thread blocking crashes
                audio = self.recognizer.listen(
                    source,
                    timeout=None,
                    phrase_time_limit=8.0
                )

            # Enforces native Swedish token interpretation
            # for core interaction flows
            return self.recognizer.recognize_google(
                audio,
                language="sv-SE"
            )

        except Exception as e:
            print(
                f"[AUDIO-DEBUG] "
                f"Audio capture transaction details: {e}"
            )

            return ""