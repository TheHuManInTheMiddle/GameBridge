# -*- coding: utf-8 -*-
"""
GameBridge User Interaction Core

ANSVAR:
 - Skapa ett unikt ID för varje human interaction.
 - Hålla interaction aktiv under dess kognitiva kedja.
 - Identifiera completion mot rätt human interaction.
 - Ingen task-sekvensering.
 - Ingen AI-logik.
 - Ingen routing.
"""

import threading
import uuid


class UserInteractionCore:
    def __init__(self):
        self._lock = threading.Lock()
        self._interactions = {}

    def start(self, user_input: str) -> str:
        """Creates a new interaction for one human input."""

        interaction_id = str(uuid.uuid4())

        with self._lock:
            self._interactions[interaction_id] = {
                "user_input": user_input,
                "active": True,
            }

        print(
            "[USER-INTERACTION] Started "
            f"interaction_id={interaction_id}"
        )

        return interaction_id

    def is_active(self, interaction_id: str) -> bool:
        """Returns whether the interaction is still active."""

        with self._lock:
            interaction = self._interactions.get(
                interaction_id
            )

            return bool(
                interaction
                and interaction.get("active", False)
            )

    def complete(self, interaction_id: str) -> None:
        """Marks one human interaction as completed."""

        with self._lock:
            interaction = self._interactions.get(
                interaction_id
            )

            if interaction:
                interaction["active"] = False

        print(
            "[USER-INTERACTION] Completed "
            f"interaction_id={interaction_id}"
        )

    def get(self, interaction_id: str):
        """Returns the stored interaction state."""

        with self._lock:
            return self._interactions.get(
                interaction_id
            )