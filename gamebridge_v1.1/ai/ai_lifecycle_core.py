# -*- coding: utf-8 -*-
"""
GameBridge AI Lifecycle Core

ANSVAR:
- Hantera AI:ns övergripande livscykel.
- Kontrollera AI/model state vid aktivering.
- Utföra model unload när AI-systemet stängs av.

EJ ANSVAR:
- Kognitiv runtime.
- Prompt-hantering.
- Ollama-kommunikation.
- GUI-logik.
- Channel 1 / Channel 2.
- Minneshantering ännu.

FRAMTIDA LIVSCYKEL:

    AI ON
        ->
    Kontrollera AI/model state
        ->
    [framtida minnesindexering / restore]
        ->
    AI READY

    AI OFF
        ->
    [framtida minnesindexering / save]
        ->
    Unload model
        ->
    AI OFF
"""

from ai.ollama_client import OllamaClient


class AILifecycleCore:
    def __init__(self, ai_client: OllamaClient):
        self.ai_client = ai_client

    def start_ai(self) -> str:
        """
        Checks the current AI/model state when GameBridge AI is
        activated.

        No model is unloaded or forcibly reloaded here.
        """

        if not self.ai_client:
            return "DISABLED"

        status = self.ai_client.check_model_status()

        print(
            "[AI-LIFECYCLE] AI activation state check: "
            f"{status}"
        )

        return status

    def unload_model(self) -> None:
        """
        Unloads the active GameBridge Ollama model.

        This is intended for the AI OFF lifecycle.
        """

        if not self.ai_client:
            return

        self.ai_client.unload_model()

    def stop_ai(self) -> None:
        """
        Executes the current AI OFF lifecycle.

        At this stage the lifecycle only unloads the model.
        Future iterations can add memory indexing and other
        shutdown stages before the unload.
        """

        print(
            "[AI-LIFECYCLE] AI shutdown sequence started."
        )

        self.unload_model()

        print(
            "[AI-LIFECYCLE] AI shutdown sequence completed."
        )