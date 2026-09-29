# -*- coding: utf-8 -*-
"""
GameBridge System TTS Provider

Provides access to locally installed Windows TTS voices through pyttsx3.
Used by the Settings GUI for dynamic TTS provider and voice discovery.
"""

import pyttsx3


def _format_voice_name(name):
    """Create a compact presentation name for system TTS voices."""
    display_name = str(name).strip()

    if display_name.startswith("Microsoft "):
        display_name = "MS " + display_name[len("Microsoft "):]

    display_name = display_name.replace(" Desktop", "", 1)

    if " - " in display_name:
        voice_name, language_name = display_name.split(" - ", 1)

        if " (" in language_name:
            language_name = language_name.split(" (", 1)[0]

        display_name = f"{voice_name} {language_name}"

    return display_name.strip()


def get_available_voices():
    """Return locally available system TTS voices."""
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")

        available_voices = []

        for voice in voices:
            name = getattr(voice, "name", None)
            voice_id = getattr(voice, "id", None)

            if not name:
                continue

            available_voices.append(
                {
                    "name": _format_voice_name(name),
                    "id": str(voice_id) if voice_id else str(name),
                }
            )

        try:
            engine.stop()
        except Exception:
            pass

        return available_voices

    except Exception as e:
        print(
            "[TTS-PROVIDER-ERROR] "
            f"Failed to enumerate system voices: {e}"
        )
        return []


def get_provider_name():
    """Return the display name of this TTS provider."""
    return "System"


def get_provider_status():
    """Return the current availability status of the system TTS provider."""
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")

        try:
            engine.stop()
        except Exception:
            pass

        if voices:
            return True

        return False

    except Exception as e:
        print(
            "[TTS-PROVIDER-ERROR] "
            f"System TTS provider unavailable: {e}"
        )
        return False