# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: None (Isolated logical data parsing boundary)
 - CALLED BY: plugins.bsf-server_plugin.main_adapter
"""

class BsfStateParser:
    """Parses raw server JSON responses into structured telemetry data for the Bridge."""
    
    @staticmethod
    def parse_messages(messages, telemetry_data, adapter_instance) -> dict:
        """Processes a list of server events and mutates telemetry state accordingly with strict hardening."""
        # HÄRDNING 1: Kontrollera att telemetrin är en fungerande ordlista
        if not isinstance(telemetry_data, dict):
            return {}
            
        if not messages:
            return telemetry_data
            
        # HÄRDNING 2: Tvinga fram en säker lista oavsett vad servern skickade
        msg_list = messages if isinstance(messages, list) else [messages]
        my_account_id = telemetry_data.get("account_id")
        
        for msg in msg_list:
            if resurrection_pack := not isinstance(msg, dict):
                continue
                
            msg_class = msg.get("class", "")
            if not isinstance(msg_class, str):
                msg_class = ""
            
            # Matchmaking match confirmed
            if "BattleCreateData" in msg_class:
                adapter_instance.battle_id = msg.get("battle_id")
                telemetry_data["battle_id"] = adapter_instance.battle_id
                telemetry_data["battle_state"] = "active"
                telemetry_data["queue_status"] = "matched"
                telemetry_data["scene"] = msg.get("scene", "greathall")
                
                # Dynamic Opponent Target Tracking Extraction
                opponent_targets = []
                
                # HÄRDNING 3: Säkra att 'parties' faktiskt är en lista innan loop
                parties = msg.get("parties")
                if isinstance(parties, list):
                    for party in parties:
                        if not isinstance(party, dict):
                            continue
                        user_id = party.get("user")
                        
                        if user_id != my_account_id:
                            # HÄRDNING 4: Säkra att enhetsdefinitionerna är en lista
                            defs = party.get("defs")
                            if isinstance(defs, list):
                                for idx, unit_def in enumerate(defs):
                                    if not isinstance(unit_def, dict):
                                        continue
                                    unit_id = unit_def.get("id")
                                    if unit_id:
                                        wire_target_str = f"{user_id}+{idx}+{unit_id}"
                                        opponent_targets.append(wire_target_str)
                                
                telemetry_data["opponent_units"] = opponent_targets
                
                # Säkert anrop till auto-ready
                if hasattr(adapter_instance, "trigger_auto_ready"):
                    adapter_instance.trigger_auto_ready()
                
            # Player readiness confirmed
            elif "BattleReadyData" in msg_class:
                pass
                
            # Active match combat synchronization turn
            elif "BattleSyncData" in msg_class:
                telemetry_data["current_turn"] = msg.get("turn", 0)
                telemetry_data["active_entity"] = msg.get("entity", "")
                
                # HÄRDNING 5: Säkra att speltiles är en lista
                if "tiles" in msg:
                    raw_tiles = msg.get("tiles")
                    telemetry_data["tiles"] = raw_tiles if isinstance(raw_tiles, list) else []
                    
        return telemetry_data
