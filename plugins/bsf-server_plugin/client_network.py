# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: None (Isolated network layer boundary)
 - CALLED BY: plugins.bsf-server_plugin.main_adapter
"""
import requests

class BsfNetworkClient:
    """Handles raw HTTP communications and polling sessions with the BSF backend server."""
    
    def __init__(self, base_url="http://localhost:8082"):
        self.base_url = base_url

    def check_health(self) -> bool:
        """Verifies if the Express backend server is alive and responding via the healthcheck vector."""
        try:
            res = requests.get(f"{self.base_url}/health", timeout=3)
            return res.status_code == 200
        except requests.RequestException:
            return False

    def login(self, username: str, steam_id: str) -> dict:
        """Performs profile authentication handshake via /services/auth/login/11."""
        url = f"{self.base_url}/services/auth/login/11"
        payload = {"username": username, "steam_id": steam_id}
        
        try:
            res = requests.post(url, json=payload, timeout=3)
            if res.status_code == 200:
                return res.json()
        except requests.RequestException:
            pass
        return {}

    def poll_updates(self, session_key: str):
        """Fetches pending live game messages and state mutations transactionally from the backend queue."""
        url = f"{self.base_url}/services/game/{session_key}"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            return res.json()
        return None
