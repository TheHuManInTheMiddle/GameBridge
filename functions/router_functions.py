# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
 - HÄMTAR FRÅN: core/path_core.py, ai/internet_transport.py, functions/internet_functions.py
 - ANROPAS AV: core/cognitive_router_core.py
"""
import json
import re
from core.path_core import PathCore
from ai.internet_transport import InternetTransport
from functions.internet_functions import function_open_browser_link

def function_pipeline_worker(router_instance, user_text: str, active_adapter, adapter_folder: str, gui_log_callback, ui_status_callback, speech_callback):
    """Manages token evaluation and execution matrix channels concurrently with capability checks."""
    try:
        ui_status_callback("PROCESSING")
        telemetry = {}
        capabilities = {}
        
        if active_adapter:
            if router_instance.io_layer:
                telemetry = router_instance.io_layer.read_from_kanal_2()
            else:
                telemetry = active_adapter.read_telemetry()
            capabilities = active_adapter.get_capabilities()

        # EXPANSION v3.0: Check if the current operational intent requires Internet AI capability
        requires_internet = capabilities.get("requires_external_ai", False)

        # Hard capability block enforcement evaluated atomically through ChannelMatrix
        if router_instance.matrix and router_instance.matrix.is_internet_blocked():
            if requires_internet:
                gui_log_callback("AI-BRIDGE (WARNING)", "Operation blocked: Target requires Internet AI, but capability is turned OFF.")
                speech_callback("Internetåtkomst är avstängd.")
                ui_status_callback("READY")
                return

        context = {
            "user_input": user_text,
            "telemetry_data": telemetry,
            "capabilities": capabilities,
            "active_adapter": active_adapter.adapter_name if active_adapter else "None",
            "channel1_chat_active": router_instance.matrix.channel1_chat_active if router_instance.matrix else False,
            "channel2_adapter_active": router_instance.matrix.channel2_adapter_active if router_instance.matrix else False
        }

        if router_instance.matrix and router_instance.matrix.is_ai_blocked():
            gui_log_callback("AI-BRIDGE (INFO)", "AI generation blocked: 'AI Active' switch is turned OFF.")
            ui_status_callback("READY")
            return

        # =========================================================================
        # EXPANSION v3.5: INTELLIGENT SÖKFILTER (Hindra fusk-sökningar på småord)
        # =========================================================================
        cleaned_input = user_text.lower().strip().strip("?!.")
        
        # Lista på vanliga hälsningar, stoppord och korta bekräftelser
        stop_words = {
            "hej", "hejsan", "hallå", "tja", "tjenare", "tjenis", "morsning", "hello", "hi", "hey",
            "ok", "okay", "okej", "yes", "ja", "nej", "no", "bra", "tack", "thanks", "grymt"
        }
        
        # Vi avgör om texten faktiskt är en informationssökning eller bara en vanlig konversation
        is_chat_only = cleaned_input in stop_words or (len(cleaned_input) < 5 and "?" not in user_text)

        # Välj transport-pipeline baserat på matrisens tillstånd OCH sökfiltret
        if router_instance.matrix and not router_instance.matrix.is_internet_blocked() and not is_chat_only:
            gui_log_callback("AI-BRIDGE (STATUS)", "Evaluating cognitive tokens via External HTTP API (:8080)...")
            transport = InternetTransport()
            ai_decision = transport.send_cognitive_request(context)
        else:
            # Om Internet AI är avstängt, ELLER om användaren bara skrev ett stoppord som "hej", kör lokalt!
            gui_log_callback("AI-BRIDGE (STATUS)", "Evaluating cognitive tokens via local HTTP API...")
            if router_instance.ai_client and hasattr(router_instance.ai_client, 'generate_response'):
                ai_decision = router_instance.ai_client.generate_response(context, adapter_folder=adapter_folder)
            else:
                ai_decision = "[AI-INFO]: Simulation deployment thread active."

        # Extract clean text for human eyes (Channel 1) and scrub local model 'response' envelopes safely
        clean_human_text = ai_decision
        if ai_decision.strip().startswith("{") and ai_decision.strip().endswith("}"):
            try:
                parsed_json = json.loads(ai_decision)
                clean_human_text = parsed_json.get("response", parsed_json.get("text", parsed_json.get("command", ai_decision)))
            except Exception:
                pass

        # Dispatch to Channel 1 (Dialogue Chat Log Box - Clean cleartext only!)
        if router_instance.matrix and router_instance.matrix.should_route_to_chat():
            if router_instance.io_layer:
                router_instance.io_layer.send_to_kanal_1("AI (Channel 1)", clean_human_text)
            else:
                gui_log_callback("AI (Channel 1)", clean_human_text)

        # Dispatch to Voice Synth (Using clean human text)
        speech_callback(clean_human_text)

        # Dispatch to Channel 2 (Dynamic Target Application Interface via exact raw JSON vectors)
        if router_instance.matrix and router_instance.matrix.should_route_to_adapter(active_adapter) and "[AI-API-ERROR]" not in ai_decision:
            gui_log_callback("AI -> CHANNEL 2", "Dispatching verified action payload to target context.")
            if router_instance.io_layer:
                router_instance.io_layer.send_to_kanal_2(ai_decision)
            else:
                active_adapter.execute_interaction(ai_decision)

    except Exception as e:
        print(f"[COGNITIVE-ROUTER-ERROR] Pipeline broken down: {e}")
    finally:
        ui_status_callback("READY")
