# -*- coding: utf-8 -*-
"""
CONNECTIONS:
  - FETCHES FROM: core/path_core.py (Absolute layout vectors)
  - CALLED BY: Dynamic core extensions and concrete adapter implementations.
"""

from abc import ABC, abstractmethod
from typing import Any
from core.path_core import PathCore

class BaseAdapter(ABC):
    def __init__(self):
        # Exposed publicly for core loader registration
        self.adapter_name = "BaseInterface"
        
        # FIXED: Core path vectors are now pulled internally to allow seamless migration
        self.project_root = PathCore.PROJECT_ROOT
        self.adapters_root = PathCore.get_adapter_root()
        
    @abstractmethod
    def initialize(self):
        """Initializes internal variables and loads localized plugin configurations."""
        pass

    @abstractmethod
    def boot_or_attach(self):
        """Asynchronously launches or attaches to the destination target application environment."""
        pass

    @abstractmethod
    def get_capabilities(self) -> dict:
        """
        Returns the plugin's unique passive or active execution capabilities.
        Uses a fluid dictionary structure to prevent hardcoding assumptions in the kernel.
        """
        pass

    @abstractmethod
    def read_telemetry(self) -> dict:
        """Reads and extracts the destination target application's current state matrix as a dict."""
        pass

    @abstractmethod
    def execute_interaction(self, action_data: Any):
        """
        Executes transaction strings, raw inputs, or command payloads against target environments.
        Supports clean JSON strings, pre-parsed dictionaries, or complex execution envelopes.
        """
        pass

    @abstractmethod
    def shutdown(self):
        """Gracefully detaches connections from targets and flushes assigned resources clean."""
        pass

