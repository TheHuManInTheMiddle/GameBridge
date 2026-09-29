# -*- coding: utf-8 -*-
"""
GameBridge Mock AI Provider

Deterministic test provider used to verify provider
selection, model selection, monitoring and GUI connections.
No real AI is used here.
"""

PROVIDER_NAME = "mock"


def get_installed_models():
    """Return deterministic mock models for provider testing."""

    return [
        "None",
        "Mock Model 1",
        "Mock Model 2",
    ]


def create_client(model_name="None"):
    """Create a deterministic mock client."""

    return MockClient(model_name)


def get_model_status(client):
    """Return a deterministic status based on the selected model."""

    if not client:
        return "ERROR"

    if client.model_name == "Mock Model 1":
        return "READY"

    if client.model_name == "Mock Model 2":
        return "NOT_READY"

    return "ERROR"


class MockClient:

    def __init__(self, model_name="None"):
        self.model_name = model_name

    def check_model_status(self):
        """Return the same deterministic status as the provider."""

        return get_model_status(self)