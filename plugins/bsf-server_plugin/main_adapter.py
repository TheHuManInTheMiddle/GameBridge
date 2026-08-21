# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
 - HÄMTAR FRÅN: adapters.base_adapter
 - HÄMTAR FRÅN: plugins.bsf-server_plugin.client_network
 - HÄMTAR FRÅN: plugins.bsf-server_plugin.state_parser
 - HÄMTAR FRÅN: plugins.bsf-server_plugin.input_handler
 - HÄMTAR FRÅN: plugins.bsf-server_plugin.intent_parser
 - ANROPAS AV: adapters.adapter_loader
 - ANROPAS AV: core.bridge_core
"""
import threading
import time
import json

# RENA V1-IMPORTER (Exakt samma mönster som Notepad-pluginen)
from adapters.base_adapter import BaseAdapter
from core.path_core import PathCore

# Lokala mappsynkade importer
from .client_network import BsfNetworkClient
from .state_parser import BsfStateParser
from .input_handler import BsfInputHandler
from .intent_parser import BsfIntentParser

class BsfServerAdapter(BaseAdapter):
    """Main Orchestrator Plugin for Banner Saga Factions server link integration."""
    
    def __init__(self):
        super().__init__()
        self.adapter_name = "BSF-Server Plugin"
        self.session_key = None
        self.account_id = None
        self.battle_id = None
        self.is_running = False
        self.active_ai_name = "AI_Autopilot"
        
        self.state_lock = threading.Lock()
        self.network = BsfNetworkClient()
        self.input_handler = BsfInputHandler()
        
        self.telemetry_data = {
            "status": "offline",
            "active_ai": self.active_ai_name,
            "account_id": None,
            "battle_id": None,
            "queue_status": "idle",
            "players_online": 0,
            "battle_state": "idle",
            "scene": None,
            "current_turn": None,
            "active_entity": None,
            "tiles": [],
            "opponent_units": []
        }
        self.poll_thread = None

    def initialize(self):
        """Resets the adapter connection matrix to a pristine startup state."""
        with self.state_lock:
            self.session_key = None
            self.account_id = None
            self.battle_id = None
            self.telemetry_data["status"] = "initialized"
            self.telemetry_data["queue_status"] = "idle"
            self.telemetry_data["opponent_units"] = []
            
            # SÄKRAD V1-SÖKVÄG: Mappar plugin_config.json direkt i v1-strukturen
            self.config_path = PathCore.get_adapter_file("bsf-server_plugin", "plugin_config.json")
            
        print(f"[{self.adapter_name}] Internationalized interface module loaded.")

    def set_active_ai(self, ai_name: str):
        """Binds the active cognitive architecture node name to telemetry tracking."""
        with self.state_lock:
            self.active_ai_name = ai_name
            self.telemetry_data["active_ai"] = ai_name
        print(f"[{self.adapter_name}] AI engine path linked: {ai_name}")

    def boot_or_attach(self) -> bool:
        """Executes hardware healthcheck and profile authentication handshakes against the Express gateway."""
        if not self.network.check_health():
            print(f"[{self.adapter_name}-ERROR] Backend /health healthcheck endpoint failed.")
            return False
            
        server_nickname = self.active_ai_name
        print(f"[{self.adapter_name}] Authenticating profile via gateway server as username: '{server_nickname}'...")
        login_data = self.network.login(server_nickname, "998877665")
        
        if login_data and isinstance(login_data, dict):
            self.session_key = login_data.get("session_key") or login_data.get("token")
            self.account_id = login_data.get("user_id")
            print(f"[{self.adapter_name}] Profile connected! Key: {self.session_key}")
        else:
            self.session_key = "debug_fallback_session_token"
            self.account_id = 343275
            print(f"[{self.adapter_name}-WARNING] Authentication rejected. Running localized fallback node.")
            
        with self.state_lock:
            self.telemetry_data["status"] = "connected"
            self.telemetry_data["account_id"] = self.account_id
            self.is_running = True
            
        self.poll_thread = threading.Thread(target=self._polling_worker, daemon=True)
        self.poll_thread.start()
        return True

    def _polling_worker(self):
        """Asynchronous background worker polling server states transactionally without blocking the UI framework."""
        while self.is_running:
            if not self.session_key:
                time.sleep(1)
                continue
            try:
                data = self.network.poll_updates(self.session_key)
                if data:
                    with self.state_lock:
                        self.telemetry_data = BsfStateParser.parse_messages(data, self.telemetry_data, self)
                        if self.telemetry_data.get("battle_id"):
                            self.battle_id = self.telemetry_data["battle_id"]
            except Exception as e:
                print(f"[{self.adapter_name}-POLL-ERROR] Connection dropped or interrupted: {e}")
            time.sleep(2)

    def trigger_auto_ready(self):
        """Asynchronously dispatches deployment sequences when a matchmaking match confirmation event fires."""
        print(f"\n[{self.adapter_name}] MATCH FOUND! Battle ID confirmed: {self.battle_id}")
        threading.Thread(
            target=self.execute_interaction,
            args=({"command": "send_ready", "battle_id": self.battle_id},),
            daemon=True
        ).start()

    def read_telemetry(self) -> dict:
        """Thread-safe telemetry snapshot reader for the core system matrix."""
        with self.state_lock:
            return dict(self.telemetry_data)

    def get_capabilities(self) -> dict:
        """Exposes operational manifest routes to core framework validation layers."""
        return {
            "capabilities": {
                "matchmaking": ["queue_start", "queue_cancel"],
                "battle_lifecycle": ["send_ready", "deploy_units", "surrender"],
                "combat_actions": ["move_unit", "execute_action"]
            }
        }

    def execute_interaction(self, action_data):
        """Main routing boundary processing raw text streams, JSON structures, and Channel 2 envelope payloads."""
        if not self.session_key:
            return
            
        command = None
        parsed_x, parsed_y = 1, 1
        parsed_action = "attack"
        parsed_target = ""
        
        if isinstance(action_data, str):
            intent_map = BsfIntentParser.parse_string(action_data)
            command = intent_map.get("command")
            parsed_x = intent_map.get("x", parsed_x)
            parsed_y = intent_map.get("y", parsed_y)
            parsed_action = intent_map.get("action", parsed_action)
            parsed_target = intent_map.get("target_id", parsed_target)
            
        if isinstance(action_data, dict):
            command = action_data.get("command", command)
            parsed_x = action_data.get("x", parsed_x)
            parsed_y = action_data.get("y", parsed_y)
            parsed_action = action_data.get("action", parsed_action)
            parsed_target = action_data.get("target_id", parsed_target)
            
        payload = action_data.get("payload", {}) if isinstance(action_data, dict) else {}
        if isinstance(payload, dict) and "decision" in payload:
            decision_str = payload.get("decision", "")
            intent_map = BsfIntentParser.parse_string(decision_str)
            command = intent_map.get("command", command)
            parsed_x = intent_map.get("x", parsed_x)
            parsed_y = intent_map.get("y", parsed_y)
            parsed_action = intent_map.get("action", parsed_action)
            parsed_target = intent_map.get("target_id", parsed_target)
            
        b_id = self.battle_id or (action_data.get("battle_id") if isinstance(action_data, dict) else None)
        current_turn = self.telemetry_data.get("current_turn", 0)
        active_entity = self.telemetry_data.get("active_entity", "")
        
        try:
            if command == "queue_start":
                print(f"[{self.adapter_name}] Transmitting matchmaking queue entry request...")
                res_data = self.input_handler.start_queue(self.session_key)
                online_count = 0
                if isinstance(res_data, list) and len(res_data) > 0:
                    status_obj = res_data[0]
                    if isinstance(status_obj, dict): 
                        online_count = status_obj.get("session_count", 0)
                elif isinstance(res_data, dict):
                    online_count = res_data.get("session_count", 0)
                    
                with self.state_lock:
                    self.telemetry_data["players_online"] = online_count
                    self.telemetry_data["queue_status"] = "searching"
                print(f"[{self.adapter_name}] Enqueued successfully. Users online: {online_count}")
                
            elif command == "send_ready":
                print(f"[{self.adapter_name}] POST -> /battle/ready for configuration sequence ID: {b_id}")
                self.input_handler.send_ready(self.session_key, b_id)
                
            elif command == "move_unit":
                print(f"[{self.adapter_name}] {self.active_ai_name} moving unit to grid position ({parsed_x}, {parsed_y})")
                self.input_handler.move_unit(self.session_key, b_id, active_entity, current_turn, parsed_x, parsed_y)
                
            elif command == "execute_action":
                print(f"[{self.adapter_name}] {self.active_ai_name} executing {parsed_action} against target {parsed_target}")
                self.input_handler.execute_action(self.session_key, b_id, active_entity, current_turn, parsed_action, parsed_target)
                
        except Exception as e:
            print(f"[{self.adapter_name}-ERROR] Interaction flow interrupted: {e}")

    def shutdown(self):
        """Gracefully terminates background long-poll networks transactionally."""
        self.is_running = False
        if self.poll_thread and self.poll_thread.is_alive():
            self.poll_thread.join(timeout=2)
        with self.state_lock:
            self.telemetry_data["status"] = "offline"
        print(f"[{self.adapter_name}] Background threads terminated cleanly.")
