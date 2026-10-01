# -*- coding: utf-8 -*-
"""
GameBridge Settings Providers

Provides dynamic lists used by the Settings GUI.
No GUI logic or runtime provider logic belongs here.
"""

import importlib
import json
import os

from core.path_core import PathCore


def _get_locales_path():
    """Return the path to the GameBridge locale configuration."""
    return PathCore.get_config_path(
        "locales.json"
    )


def _get_providers_path():
    """Return the path to the GameBridge provider directory."""
    return PathCore.get_provider_root()


def get_supported_languages():
    """Return language codes defined in config/locales.json."""
    try:
        with open(
            _get_locales_path(),
            "r",
            encoding="utf-8"
        ) as file:
            locales = json.load(file)

        if not isinstance(locales, dict):
            return []

        return list(locales.keys())

    except (OSError, json.JSONDecodeError):
        return []


def get_tts_providers():
    """Return available TTS providers from the provider directory."""
    try:
        providers_path = _get_providers_path()

        if not os.path.isdir(providers_path):
            return []

        providers = []

        for filename in os.listdir(providers_path):
            if (
                filename.endswith("_tts.py")
                and filename != "__init__.py"
            ):
                providers.append(
                    filename[:-len("_tts.py")]
                )

        return sorted(providers)

    except OSError:
        return []


def get_available_voices(provider):
    """Return voices available from the selected TTS provider."""
    if not provider or provider == "none":
        return []

    try:
        module_name = f"providers.{provider}_tts"

        module = importlib.import_module(
            module_name
        )

        get_voices = getattr(
            module,
            "get_available_voices",
            None
        )

        if not callable(get_voices):
            return []

        voices = get_voices()

        if not isinstance(voices, list):
            return []

        return voices

    except (
        ImportError,
        AttributeError,
        OSError
    ):
        return []


def get_internet_providers():
    """Return available Internet providers."""
    try:
        providers_path = _get_providers_path()

        if not os.path.isdir(providers_path):
            return []

        providers = []

        for filename in os.listdir(providers_path):
            if (
                filename.endswith("_provider.py")
                and filename != "__init__.py"
            ):
                providers.append(
                    filename[:-len("_provider.py")]
                )

        return sorted(providers)

    except OSError:
        return []


def get_ai_providers():
    """Return available AI providers from the provider directory."""
    try:
        providers_path = _get_providers_path()

        if not os.path.isdir(providers_path):
            return []

        providers = []

        for filename in os.listdir(providers_path):
            if (
                filename.endswith("_ai.py")
                and filename != "__init__.py"
            ):
                providers.append(
                    filename[:-len("_ai.py")]
                )

        return sorted(providers)

    except OSError:
        return []