# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
  - ANVÄNDS AV: GameBridge runtime
  - PÅVERKAR: Centrala runtime states

ANSVAR:
  - Äga GameBridge centrala runtime switch-states.
  - Vara oberoende av GUI och adapters.
"""


class RuntimeStateCore:
    """Central owner for GameBridge runtime state."""

    def __init__(self):
        self._state = {
            "ai_active": False,
            "internet_ai_active": False,
            "channel1_active": False,
            "ai_channel1_active": True,
            "ai_voice_active": False,
            "user_voice_active": False,
            "voice_mode": "OFF",
            "channel2_active": False,
            "telemetry_active": False,
            "locked": False,
            "duplicate_plugin": False,
            "duplicate_plugin_path": None,
        }

    def get_state(self, key: str, default=None):
        """Return the current value of a runtime state."""

        return self._state.get(
            key,
            default
        )

    def set_state(self, key: str, value):
        """Set the value of a runtime state."""

        self._state[key] = value

    def get_all_states(self) -> dict:
        """Return a copy of the complete runtime state."""

        return dict(
            self._state
        )

    def clear_state(self, key: str):
        """Remove a runtime state value when present."""

        self._state.pop(
            key,
            None
        )