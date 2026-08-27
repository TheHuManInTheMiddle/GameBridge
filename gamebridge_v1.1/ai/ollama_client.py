# -*- coding: utf-8 -*-
"""
CONNECTIONS:
  - FETCHES FROM: Dynamic system_prompt.txt paths within plugins/
  - CALLED BY: src/main.py, src/core/channel_matrix.py (State evaluation triggers)
"""

import json
import os
import urllib.request
import urllib.error


class OllamaClient:
    def __init__(
        self,
        model_name: str = "None",
        base_url: str = "http://localhost:11434",
    ):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self.show_url = f"{base_url}/api/show"

    def check_model_status(self) -> str:
        """
        Queries the local Ollama instance to track current model
        availability state.

        "None" is an explicit disabled state and must never be sent
        to Ollama as a model name.
        """

        if not self.model_name or self.model_name == "None":
            return "DISABLED"

        payload = {"name": self.model_name}

        try:
            data = json.dumps(payload).encode("utf-8")

            req = urllib.request.Request(
                self.show_url,
                data=data,
                headers={
                    "Content-Type": "application/json"
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    return "READY"

        except urllib.error.URLError:
            return "OFFLINE"

        except Exception:
            return "LOADING"

        return "OFFLINE"

    def _load_adapter_system_prompt(
        self,
        adapter_folder: str,
    ) -> str:
        """
        Reads the extension's system_prompt.txt dynamically from disk
        using relative paths.
        """

        if not adapter_folder or adapter_folder == "None":
            return (
                "You are the G.A.M.E. B.R.I.D.G.E. AI framework. "
                "No extension target is currently active."
            )

        prompt_path = os.path.join(
            "plugins",
            adapter_folder,
            "system_prompt.txt",
        )

        if os.path.exists(prompt_path):
            try:
                with open(
                    prompt_path,
                    "r",
                    encoding="utf-8",
                ) as f:
                    return f.read().strip()

            except Exception as e:
                print(
                    "[AI-ERROR] Failed to load local system "
                    f"prompt vector from '{prompt_path}': {e}"
                )

        return (
            "You are an AI integrated via G.A.M.E. B.R.I.D.G.E. "
            "Act as a generalized runtime assistant."
        )

    def generate_response(
        self,
        context: dict,
        adapter_folder: str = "None",
    ) -> str:
        """
        Evaluates token contexts across Channel 1 and Channel 2
        dispatch guidelines with forced JSON boundaries.

        If no Ollama model is selected, no request is sent to Ollama.
        """

        # ----------------------------------------------------------
        # MODEL GATE
        # ----------------------------------------------------------
        # "None" is a legitimate state, not an Ollama model.
        # Do not construct or send an API request in this state.
        # ----------------------------------------------------------

        if not self.model_name or self.model_name == "None":
            return "[AI-DISABLED] No Ollama model selected."

        user_input = context.get(
            "user_input",
            "",
        )

        telemetry = context.get(
            "telemetry_data",
            {},
        )

        capabilities = context.get(
            "capabilities",
            {},
        )

        base_system_prompt = self._load_adapter_system_prompt(
            adapter_folder
        )

        k1_chat = context.get(
            "channel1_chat_active",
            False,
        )

        k2_adapter = context.get(
            "channel2_adapter_active",
            False,
        )

        channel_instructions = (
            "\n\n[ACTIVE INTERACTION PROFILE STATE]\n"
        )

        if k1_chat and k2_adapter:

            channel_instructions += (
                "Channel 1 (Dialogue Chat) and Channel 2 "
                "(Target App Adapter) are active. "
                "Engage in human dialogue and execute requested "
                "environmental interactions concurrently. "
                "You MUST return your answer inside a valid "
                "JSON object structure."
            )

        elif k1_chat and not k2_adapter:

            channel_instructions += (
                "Channel 1 (Dialogue Chat) is active. "
                "Channel 2 (Target App Adapter) is locked. "
                "Pure conversational dialogue state. "
                "Do not emit machine execution codes or "
                "interface modifications."
            )

        elif not k1_chat and k2_adapter:

            channel_instructions += (
                "Channel 1 (Dialogue Chat) is locked. "
                "Channel 2 (Target App Adapter) is active. "
                "Focus entirely on automated app interactions. "
                "Respond with short, raw execution payload "
                "text decisions only."
            )

        else:

            channel_instructions += (
                "All routing vectors suspended."
            )

        full_system_prompt = (
            f"{base_system_prompt}"
            f"{channel_instructions}\n\n"
            f"Available extension capabilities matrix:\n"
            f"{json.dumps(capabilities, indent=2)}\n\n"
            f"Active telemetry data streams from destination context:\n"
            f"{json.dumps(telemetry, indent=2)}"
        )

        # Enforce highly deterministic responses when adapter
        # manipulation is active.
        target_temp = (
            0.1
            if k2_adapter
            else 0.3
        )

        payload = {
            "model": self.model_name,
            "prompt": user_input,
            "system": full_system_prompt,
            "stream": False,
            "options": {
                "temperature": target_temp
            },
        }

        # Hardcoded grammar barrier lock via Ollama native API parameter.
        if k2_adapter:
            payload["format"] = "json"

        try:

            data = json.dumps(
                payload
            ).encode("utf-8")

            req = urllib.request.Request(
                self.api_url,
                data=data,
                headers={
                    "Content-Type": "application/json"
                },
                method="POST",
            )

            with urllib.request.urlopen(
                req,
                timeout=90,
            ) as response:

                response_data = json.loads(
                    response.read().decode("utf-8")
                )

                return response_data.get(
                    "response",
                    "",
                ).strip()

        except urllib.error.URLError as e:

            print(
                "[AI-API-ERROR] Communications block failed "
                "to resolve Ollama loopback endpoint: "
                f"{e}"
            )

            return (
                "[AI-API-ERROR] Local Ollama instances "
                "are currently unresponsive."
            )

        except Exception as e:

            print(
                "[AI-API-ERROR] Critical execution exception: "
                f"{e}"
            )

            return (
                "[AI-API-ERROR] Internal system AI client "
                "exception."
            )