# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: None (Isolated network command execution boundary)
 - CALLED BY: plugins.bsf-server_plugin.main_adapter
"""
import requests
import time

class BsfInputHandler:
    """Translates high-level interaction intents into actionable POST commands mapping to the BSF server API schema."""
    
    def __init__(self, base_url="http://localhost:8082"):
        self.base_url = base_url

    def start_queue(self, session_key: str) -> dict:
        """Posts a competitive matchmaking search request via the vs/start endpoint."""
        url = f"{self.base_url}/services/vs/start/{session_key}"
        payload = {"power": 6, "vs_type": "QUICK"}
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            return res.json()
        return {}

    def send_ready(self, session_key: str, battle_id: str):
        """Signals readiness and transactionally transmits the initial 6-viking tactical deploy matrix layout."""
        ready_url = f"{self.base_url}/services/battle/ready/{session_key}"
        requests.post(ready_url, json={"battle_id": battle_id}, timeout=3)
        
        # Deployment tactical positions offset matrix instantiation
        deploy_url = f"{self.base_url}/services/battle/deploy/{session_key}"
        deploy_payload = {
            "battle_id": battle_id,
            "tiles": [
                {"class": "tbs.srv.battle.data.Tile", "x": 1, "y": 1},
                {"class": "tbs.srv.battle.data.Tile", "x": 1, "y": 2},
                {"class": "tbs.srv.battle.data.Tile", "x": 1, "y": 3},
                {"class": "tbs.srv.battle.data.Tile", "x": 2, "y": 1},
                {"class": "tbs.srv.battle.data.Tile", "x": 2, "y": 2},
                {"class": "tbs.srv.battle.data.Tile", "x": 2, "y": 3}
            ]
        }
        requests.post(deploy_url, json=deploy_payload, timeout=3)

    def move_unit(self, session_key: str, battle_id: str, entity: str, turn: int, x: int, y: int):
        """Posts a tactical movement grid update to the battle sync pipeline utilizing strict telemetry schemas."""
        url = f"{self.base_url}/services/battle/move/{session_key}"
        payload = {
            "class": "tbs.srv.battle.data.client.BattleSyncData",
            "timestamp": int(time.time() * 1000),
            "battle_id": battle_id,
            "entity": entity,
            "turn": turn,
            "ordinal": 1,
            "tiles": [
                {"class": "tbs.srv.battle.data.Tile", "x": x, "y": y}
            ]
        }
        requests.post(url, json=payload, timeout=3)

    def execute_action(self, session_key: str, battle_id: str, entity: str, turn: int, action: str, target_id: str):
        """Posts a combat or ability action targeting an opposing entity array transactionally."""
        url = f"{self.base_url}/services/battle/action/{session_key}"
        payload = {
            "class": "tbs.srv.battle.data.client.BattleActionData",
            "timestamp": int(time.time() * 1000),
            "battle_id": battle_id,
            "entity": entity,
            "turn": turn,
            "ordinal": 2,
            "terminator": True,
            "action": action,
            "executed_id": 0,
            "level": 1,
            "tiles": [],
            "target_ids": [target_id]
        }
        requests.post(url, json=payload, timeout=3)

    def cancel_queue(self, session_key: str):
        """Cancels an active matchmaking queue search sequence."""
        url = f"{self.base_url}/services/vs/cancel/{session_key}"
        requests.post(url, json={}, timeout=3)
