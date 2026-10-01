# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
 - HÄMTAR FRÅN: core/path_core.py, ai/internet_transport.py, functions/internet_functions.py
 - ANROPAS AV: core/cognitive_router_core.py

ANSVAR:
 - Hantera GameBridges funktionella routing-pipeline.
 - Kontrollera capabilities och channel-matrix.
 - Avgöra om extern internetåtkomst ska användas.
 - Läsa denied_search_phrases från extern config.
 - Separera mänsklig chat-output från Channel 2:s maskinpayload.
 - Channel 2-action ska inte läcka till Channel 1.
 - Råda AI/User-output till Channel 1 eller RAW enligt RuntimeStateCore.
 - Hålla AI Voice/TTS separat från text-routing.
 - Behålla övrig routinglogik oförändrad.
"""

import json
import re

from core.path_core import PathCore
from ai.internet_transport import InternetTransport
from functions.internet_functions import function_open_browser_link


def _load_denied_search_phrases() -> set:
    """
    Läser GameBridges externa lista över fraser som inte ska
    trigga extern internetsökning.

    Filen ligger i:
        config/denied_search_phrases.json

    Förväntat format:
        {
            "phrases": [
                "hej",
                "hallå",
                "hello"
            ]
        }

    Om filen saknas eller är ogiltig returneras en tom mängd
    så att routing-pipelinen inte kraschar.
    """

    config_path = PathCore.get_config_path(
        "denied_search_phrases.json"
    )

    try:
        with open(
            config_path,
            "r",
            encoding="utf-8"
        ) as config_file:

            data = json.load(config_file)

        phrases = data.get(
            "phrases",
            []
        )

        if not isinstance(phrases, list):
            return set()

        return {
            str(phrase).strip().lower()
            for phrase in phrases
            if str(phrase).strip()
        }

    except (
        OSError,
        json.JSONDecodeError,
        TypeError,
        AttributeError
    ) as exc:

        print(
            "[!] [ROUTER] Kunde inte läsa "
            f"denied_search_phrases.json: {exc}"
        )

        return set()


def function_route_user_voice(
    router_instance,
    recognized_text: str,
    gui_log_callback
):
    """
    Dum routing för User Voice/STT-output.

    RuntimeStateCore avgör endast destination:
        channel1_active = True  -> Channel 1
        channel1_active = False -> RAW

    Denna funktion påverkar inte AI-input.
    Det transkriberade talet skickas fortfarande
    till process_chatt_flow() av anropande lager.
    """

    if not recognized_text:
        return

    channel1_active = (
        router_instance.core_parent.runtime_state.get_state(
            "channel1_active",
            False
        )
        if (
            router_instance.core_parent
            and router_instance.core_parent.runtime_state
        )
        else False
    )

    if (
        router_instance.core_parent
        and router_instance.core_parent.gui
        and getattr(
            router_instance.core_parent.gui,
            "system_lang",
            "en"
        ) == "sv"
    ):
        sender_tag = "ANVÄNDARE (Kanal 1)"
    else:
        sender_tag = "USER (Channel 1)"

    if channel1_active:

        if router_instance.io_layer:

            router_instance.io_layer.send_to_kanal_1(
                sender_tag,
                recognized_text
            )

        else:

            gui_log_callback(
                sender_tag,
                recognized_text
            )

    else:

        gui_log_callback(
            "RAW",
            recognized_text
        )


def function_route_ai_text(
    router_instance,
    clean_human_text: str,
    gui_log_callback
):
    """
    Dum routing för AI:s text-output.

    RuntimeStateCore avgör endast destination:
        ai_channel1_active = True  -> Channel 1
        ai_channel1_active = False -> RAW

    TTS hanteras separat via speech_callback och påverkas
    inte av denna text-routing.
    """

    if not clean_human_text:
        return

    ai_channel1_active = (
        router_instance.core_parent.runtime_state.get_state(
            "ai_channel1_active",
            False
        )
        if (
            router_instance.core_parent
            and router_instance.core_parent.runtime_state
        )
        else False
    )

    if ai_channel1_active:

        if router_instance.io_layer:

            router_instance.io_layer.send_to_kanal_1(
                "AI (Channel 1)",
                clean_human_text
            )

        else:

            gui_log_callback(
                "AI (Channel 1)",
                clean_human_text
            )

    else:

        gui_log_callback(
            "RAW",
            clean_human_text
        )


def function_pipeline_worker(
    router_instance,
    user_text: str,
    active_adapter,
    adapter_folder: str,
    gui_log_callback,
    ui_status_callback,
    speech_callback,
    interaction_id=None
):
    """
    Manages token evaluation and execution matrix channels.
    """

    try:
        ui_status_callback("PROCESSING")

        telemetry = {}
        capabilities = {}

        telemetry_active = (
            router_instance.core_parent.runtime_state.get_state(
                "telemetry_active",
                False
            )
            if (
                router_instance.core_parent
                and router_instance.core_parent.runtime_state
            )
            else False
        )

        if active_adapter and telemetry_active:

            # REN FIX:
            # Prioritera adapterns egna read_telemetry()
            # för kanal-2 data.
            if hasattr(
                active_adapter,
                "read_telemetry"
            ):
                telemetry = active_adapter.read_telemetry()

            elif router_instance.io_layer:
                telemetry = (
                    router_instance.io_layer
                    .read_from_kanal_2()
                )

        if active_adapter:

            capabilities = (
                active_adapter.get_capabilities()
            )

        # EXPANSION v3.0:
        # Check if the current operational intent requires
        # Internet AI capability.

        requires_internet = capabilities.get(
            "requires_external_ai",
            False
        )

        # Hard capability block enforcement evaluated
        # atomically through ChannelMatrix.

        if (
            router_instance.matrix
            and router_instance.matrix.is_internet_blocked()
        ):

            if requires_internet:

                gui_log_callback(
                    "AI-BRIDGE (WARNING)",
                    "Operation blocked: Target requires "
                    "Internet AI, but capability is turned OFF."
                )

                ui_status_callback("READY")
                return

        # =====================================================================
        # RAW ACL
        # =====================================================================
        #
        # Channel 1 är alltid läsbar för AI.
        #
        # RAW får AI endast läsa när:
        #   user_voice_active == True
        #   AND
        #   channel1_active == False
        #
        # Om Channel 1 är avstängd och User Voice också är avstängd
        # ska RAW inte lämnas vidare till AI.
        # =====================================================================

        user_voice_active = (
            router_instance.core_parent.runtime_state.get_state(
                "user_voice_active",
                False
            )
            if (
                router_instance.core_parent
                and router_instance.core_parent.runtime_state
            )
            else False
        )

        channel1_active = (
            router_instance.core_parent.runtime_state.get_state(
                "channel1_active",
                False
            )
            if (
                router_instance.core_parent
                and router_instance.core_parent.runtime_state
            )
            else False
        )

        ai_can_read_raw = (
            user_voice_active
            and not channel1_active
        )

        if (
            not channel1_active
            and not ai_can_read_raw
        ):

            ui_status_callback("READY")
            return

        context = {
            "user_input": user_text,
            "interaction_id": interaction_id,
            "telemetry_data": telemetry,
            "capabilities": capabilities,
            "active_adapter": (
                active_adapter.adapter_name
                if active_adapter
                else "None"
            ),
            "ai_channel1_active": (
                router_instance.core_parent.runtime_state.get_state(
                    "ai_channel1_active",
                    False
                )
                if (
                    router_instance.core_parent
                    and router_instance.core_parent.runtime_state
                )
                else False
            ),
            "channel2_adapter_active": (
                router_instance.matrix.channel2_adapter_active
                if router_instance.matrix
                else False
            )
        }

        if (
            router_instance.matrix
            and router_instance.matrix.is_ai_blocked()
        ):

            gui_log_callback(
                "AI-BRIDGE (INFO)",
                "AI generation blocked: "
                "'AI Active' switch is turned OFF."
            )

            ui_status_callback("READY")
            return

        # =========================================================================
        # EXPANSION v3.5:
        # INTELLIGENT SÖKFILTER
        # =========================================================================

        cleaned_input = (
            user_text
            .lower()
            .strip()
            .strip("?!.")
        )

        denied_search_phrases = (
            _load_denied_search_phrases()
        )

        # Vi avgör om texten faktiskt är en informationssökning
        # eller bara vanlig konversation.

        is_chat_only = (
            cleaned_input in denied_search_phrases
            or (
                len(cleaned_input) < 5
                and "?" not in user_text
            )
        )

        # Välj transport-pipeline baserat på matrisens tillstånd
        # OCH sökfiltret.

        if (
            router_instance.matrix
            and not router_instance.matrix.is_internet_blocked()
            and not is_chat_only
        ):

            gui_log_callback(
                "AI-BRIDGE (STATUS)",
                "Evaluating cognitive tokens via "
                "External HTTP API (:8080)..."
            )

            transport = InternetTransport()

            ai_decision = (
                transport.send_cognitive_request(
                    context
                )
            )

        else:

            # Om Internet AI är avstängt, ELLER om användaren
            # bara skrev ett stoppord som "hej", kör lokalt.

            gui_log_callback(
                "AI-BRIDGE (STATUS)",
                "Evaluating cognitive tokens via "
                "local HTTP API..."
            )

            if (
                router_instance.ai_client
                and hasattr(
                    router_instance.ai_client,
                    "generate_response"
                )
            ):

                ai_decision = (
                    router_instance.ai_client
                    .generate_response(
                        context,
                        adapter_folder=adapter_folder
                    )
                )

            else:

                ai_decision = (
                    "[AI-INFO]: "
                    "Simulation deployment thread active."
                )

        # =========================================================================
        # RUNTIME DISPATCH
        # =========================================================================
        #
        # OllamaClient äger runtime.
        #
        # function_pipeline_worker gör endast:
        #
        #   1. ta emot aktuellt steg
        #   2. dispatcha steget
        #   3. returnera GameBridge-kvittot
        #   4. lämna över nästa steg till samma runtime
        #
        # Ingen kognitiv sekvenslogik finns här.
        # =========================================================================

        while True:

            # =====================================================================
            # OUTPUT SEPARATION
            # =====================================================================

            clean_human_text = ""
            channel2_payload = None
            telemetry_request = None
            is_channel2_action = False
            is_telemetry_request = False

            if (
                isinstance(ai_decision, str)
                and ai_decision.strip().startswith("{")
                and ai_decision.strip().endswith("}")
            ):

                try:

                    parsed_json = json.loads(
                        ai_decision
                    )

                    if isinstance(parsed_json, dict):

                        # ---------------------------------------------------------
                        # TELEMETRY REQUEST
                        # ---------------------------------------------------------
                        #
                        # Provider-neutral GameBridge request.
                        #
                        # Ollama provider returns the semantic tool request
                        # without executing it. GameBridge executes the
                        # fallback tool here and returns a receipt through
                        # continue_runtime().
                        # ---------------------------------------------------------

                        if (
                            parsed_json.get("tool")
                            == (
                                getattr(
                                    router_instance.ai_client,
                                    "TOOL_TELEMETRY",
                                    "gamebridge_telemetry"
                                )
                            )
                        ):

                            is_telemetry_request = True

                            telemetry_request = parsed_json

                        # ---------------------------------------------------------
                        # CHANNEL 2 ACTION
                        # ---------------------------------------------------------

                        elif (
                            isinstance(
                                parsed_json.get("action"),
                                str
                            )
                            and parsed_json.get("action").strip()
                        ):

                            is_channel2_action = True
                            channel2_payload = parsed_json

                        else:

                            human_response = parsed_json.get(
                                "response",
                                parsed_json.get(
                                    "text",
                                    ""
                                )
                            )

                            if isinstance(
                                human_response,
                                str
                            ):

                                clean_human_text = (
                                    human_response.strip()
                                )

                            elif human_response is not None:

                                clean_human_text = str(
                                    human_response
                                ).strip()

                except (
                    json.JSONDecodeError,
                    TypeError,
                    AttributeError
                ):

                    clean_human_text = ""

            else:

                # Vanlig AI-text går till routern för
                # destination enligt RuntimeStateCore.

                clean_human_text = (
                    ai_decision
                    if isinstance(
                        ai_decision,
                        str
                    )
                    else str(ai_decision)
                )

            # =====================================================================
            # TEXT ROUTING
            # =====================================================================

            if (
                not is_channel2_action
                and not is_telemetry_request
                and clean_human_text
            ):

                function_route_ai_text(
                    router_instance,
                    clean_human_text,
                    gui_log_callback
                )

            # =====================================================================
            # VOICE
            # =====================================================================

            if (
                not is_channel2_action
                and not is_telemetry_request
                and clean_human_text
            ):

                speech_callback(
                    clean_human_text
                )

            # =====================================================================
            # TELEMETRY
            # =====================================================================

            telemetry_receipt = None

            if (
                is_telemetry_request
                and router_instance.ai_client
                and hasattr(
                    router_instance.ai_client,
                    "execute_gamebridge_tool"
                )
            ):

                print(
                    "[AI-RUNTIME] GameBridge telemetry fallback "
                    "executing requested read."
                )

                try:

                    telemetry_data = (
                        router_instance.ai_client
                        .execute_gamebridge_tool(
                            router_instance.ai_client.TOOL_TELEMETRY,
                            telemetry_request.get(
                                "arguments",
                                {}
                            )
                        )
                    )

                    if telemetry_data is None:

                        telemetry_data = {
                            "status": "unavailable"
                        }

                    telemetry_receipt = {
                        "status": "completed",
                        "step": "telemetry",
                        "data": telemetry_data
                    }

                except Exception as e:

                    print(
                        "[COGNITIVE-ROUTER-ERROR] "
                        "Telemetry execution failed: "
                        f"{e}"
                    )

                    telemetry_receipt = {
                        "status": "failed",
                        "step": "telemetry"
                    }

            # =====================================================================
            # CHANNEL 2
            # =====================================================================

            channel2_receipt = None

            if (
                channel2_payload is not None
                and router_instance.matrix
                and router_instance.matrix.should_route_to_adapter(
                    active_adapter
                )
            ):

                gui_log_callback(
                    "AI -> CHANNEL 2",
                    "Dispatching verified action payload "
                    "to target context."
                )

                if router_instance.io_layer:

                    router_instance.io_layer.send_to_kanal_2(
                        channel2_payload
                    )

                else:

                    active_adapter.execute_interaction(
                        channel2_payload
                    )

                # GameBridge-side dispatch receipt.
                #
                # This means GameBridge has dispatched the
                # payload. It does NOT mean that the target
                # application has confirmed execution.

                channel2_receipt = {
                    "status": "dispatched"
                }

            # =====================================================================
            # RUNTIME CONTINUATION
            # =====================================================================
            #
            # Channel 2:
            #   GameBridge returns its dispatch receipt.
            #
            # Telemetry:
            #   GameBridge returns its completed read receipt.
            #
            # Other steps:
            #   Preserve the existing completion behaviour.
            #
            # OllamaClient decides whether another cognitive
            # step is required.
            # =====================================================================

            if (
                router_instance.ai_client
                and hasattr(
                    router_instance.ai_client,
                    "continue_runtime"
                )
            ):

                if telemetry_receipt is not None:

                    ai_decision = (
                        router_instance.ai_client
                        .continue_runtime(
                            completion=telemetry_receipt
                        )
                    )

                elif channel2_receipt is not None:

                    ai_decision = (
                        router_instance.ai_client
                        .continue_runtime(
                            completion=channel2_receipt
                        )
                    )

                else:

                    ai_decision = (
                        router_instance.ai_client
                        .continue_runtime(
                            completion={
                                "status": "completed"
                            }
                        )
                    )

                if not ai_decision:
                    break

                continue

            break

    except Exception as e:

        print(
            "[COGNITIVE-ROUTER-ERROR] "
            f"Pipeline broken down: {e}"
        )

    finally:

        ui_status_callback("READY")