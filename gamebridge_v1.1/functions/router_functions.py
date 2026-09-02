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


def function_pipeline_worker(
    router_instance,
    user_text: str,
    active_adapter,
    adapter_folder: str,
    gui_log_callback,
    ui_status_callback,
    speech_callback
):
    """
    Manages token evaluation and execution matrix channels
    concurrently with capability checks.
    """

    try:
        ui_status_callback("PROCESSING")

        telemetry = {}
        capabilities = {}

        if active_adapter:

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

        context = {
            "user_input": user_text,
            "telemetry_data": telemetry,
            "capabilities": capabilities,
            "active_adapter": (
                active_adapter.adapter_name
                if active_adapter
                else "None"
            ),
            "channel1_chat_active": (
                router_instance.matrix.channel1_chat_active
                if router_instance.matrix
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
        # OUTPUT SEPARATION
        # =========================================================================
        #
        # Channel 2 använder den strukturerade payload som AI:n producerar.
        #
        # action/text är en del av den befintliga adapter-payloaden och
        # ska därför inte filtreras bort eller tolkas om här.
        #
        # Rå AI-output får däremot inte samtidigt läcka till Channel 1.
        # =========================================================================

        clean_human_text = ""
        channel2_payload = None
        is_channel2_action = False

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

                    # En strukturerad JSON-payload med action är
                    # maskindata för Channel 2.
                    #
                    # Payloaden lämnas intakt så att adaptern får
                    # översätta den till målmiljöns format.

                    if (
                        isinstance(
                            parsed_json.get("action"),
                            str
                        )
                        and parsed_json.get("action").strip()
                    ):

                        is_channel2_action = True
                        channel2_payload = parsed_json

                    # JSON utan action behandlas inte som Channel 2-action.
                    # Eventuell human-readable response kan visas i Channel 1.

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

                # Ogiltig JSON ska inte skickas som maskinpayload.
                clean_human_text = ""

        else:

            # Vanlig AI-text går fortsatt till Channel 1.

            clean_human_text = (
                ai_decision
                if isinstance(
                    ai_decision,
                    str
                )
                else str(ai_decision)
            )

        # =========================================================================
        # CHANNEL 1
        # =========================================================================

        if (
            not is_channel2_action
            and router_instance.matrix
            and router_instance.matrix.should_route_to_chat()
            and clean_human_text
        ):

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

        # =========================================================================
        # VOICE
        # =========================================================================

        if (
            not is_channel2_action
            and clean_human_text
        ):

            speech_callback(
                clean_human_text
            )

        # =========================================================================
        # CHANNEL 2
        # =========================================================================
        #
        # Channel 2 får endast den strukturerade payloaden.
        #
        # Rå ai_decision skickas aldrig direkt till Channel 2.
        #
        # Payloadens innehåll lämnas till adaptern.
        # Adaptern ansvarar för översättning till målmiljöns format.
        # =========================================================================

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

    except Exception as e:

        print(
            "[COGNITIVE-ROUTER-ERROR] "
            f"Pipeline broken down: {e}"
        )

    finally:

        ui_status_callback("READY")