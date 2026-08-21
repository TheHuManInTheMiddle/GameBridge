# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: None (Isolated intent analytics frame)
 - CALLED BY: plugins.bsf-server_plugin.main_adapter
"""
import re

class BsfIntentParser:
    """Parses raw alphanumeric cognitive text streams into functional operational command dicts."""
    
    @staticmethod
    def parse_string(action_string: str) -> dict:
        """Applies text parsing regex patterns to extract commands, coordinates, actions, and combat targets."""
        cleaned = (action_string or "").strip().lower()
        intent = {
            "command": None,
            "x": 1,
            "y": 1,
            "action": "attack",
            "target_id": ""
        }
        
        # 1. Matchmaking / Lifecycle intents
        if "queue_start" in cleaned or "sök match" in cleaned or "starta kö" in cleaned:
            intent["command"] = "queue_start"
            return intent
        if "send_ready" in cleaned or "redo" in cleaned:
            intent["command"] = "send_ready"
            return intent
            
        # 2. Tactical Movement Intents (e.g., "move_unit(x=3, y=5)")
        if "move_unit" in cleaned or "flytta" in cleaned:
            intent["command"] = "move_unit"
            x_match = re.search(r'x\s*=\s*(\d+)', cleaned)
            y_match = re.search(r'y\s*=\s*(\d+)', cleaned)
            if x_match:
                intent["x"] = int(x_match.group(1))
            if y_match:
                intent["y"] = int(y_match.group(1))
            return intent
            
        # 3. Action / Combat Intents (e.g., "execute_action(action=attack, target=123)")
        if "execute_action" in cleaned or "attack" in cleaned or "anfall" in cleaned:
            intent["command"] = "execute_action"
            act_match = re.search(r'action\s*=\s*([a-z_]+)', cleaned)
            tar_match = re.search(r'target(?:_id)?\s*=\s*([a-z0-9_\+]+)', cleaned)
            if act_match:
                intent["action"] = act_match.group(1)
            if tar_match:
                intent["target_id"] = tar_match.group(1).upper()
            return intent
            
        return intent
