# -*- coding: utf-8 -*-
"""
GameBridge Ollama AI Provider

Provider adapter for Ollama.

Contains:
- Ollama provider discovery
- Ollama model management
- OllamaClient runtime implementation

No GUI logic belongs here.

GameBridge semantics are inherited from AIBase.
Provider-specific communication and runtime behavior
remain inside this provider.
"""

import json
import os
import urllib.request
import urllib.error

from core.path_core import PathCore
from ai.ai_base import AIBase


PROVIDER_NAME = "ollama"


# ======================================================================
# PROVIDER DISCOVERY
# ======================================================================

def get_installed_models():
    """Return models installed in the local Ollama instance."""

    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/tags",
            headers={
                "Content-Type": "application/json"
            },
            method="GET",
        )

        with urllib.request.urlopen(
            req,
            timeout=5,
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        models = [
            model["name"]
            for model in data.get("models", [])
            if model.get("name")
        ]

        return ["None"] + models

    except Exception as e:
        print(
            "[OLLAMA-DISCOVERY] Failed to fetch installed models: "
            f"{e}"
        )
        return ["None"]


def create_client(model_name="None"):
    """Create the GameBridge Ollama client."""

    return OllamaClient(
        model_name=model_name
    )


def get_model_status(client):
    """Return the current status from the Ollama client."""

    if not client:
        return "ERROR"

    try:
        return client.check_model_status()

    except Exception:
        return "ERROR"


# ======================================================================
# OLLAMA CLIENT
# ======================================================================

class OllamaClient(AIBase):
    def __init__(
        self,
        model_name: str = "None",
        base_url: str = "http://localhost:11434",
    ):
        super().__init__()

        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/chat"
        self.show_url = f"{base_url}/api/show"

    # ==================================================================
    # MODEL STATUS
    # ==================================================================

    def check_model_status(self) -> str:
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

    # ==================================================================
    # GAMEBRIDGE PROMPT SOURCES
    # ==================================================================

    def _load_gamebridge_system_prompt(self) -> str:
        prompt_path = PathCore.get_config_path(
            "system_prompt.txt"
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
                    "[AI-ERROR] Failed to load GameBridge "
                    f"system prompt from '{prompt_path}': {e}"
                )

        return (
            "You are the AI cognitive core of "
            "G.A.M.E. B.R.I.D.G.E."
        )

    def _load_plugin_prompt(
        self,
        adapter_folder: str,
    ) -> str:

        if not adapter_folder or adapter_folder == "None":
            return (
                "No extension target is currently active."
            )

        prompt_path = PathCore.get_adapter_file(
            adapter_folder,
            "plugin_prompt.txt",
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
                    "[AI-ERROR] Failed to load plugin "
                    f"prompt from '{prompt_path}': {e}"
                )

        return (
            "No plugin-specific instructions "
            "are currently available."
        )

    # ==================================================================
    # MODEL LIFECYCLE
    # ==================================================================

    def unload_model(self) -> None:
        """
        Unloads the active Ollama model from runtime memory.

        This is intentionally separate from stop_runtime().

        stop_runtime() ends one cognitive interaction.
        unload_model() is used when the AI lifecycle itself is
        switched off.
        """

        if not self.model_name or self.model_name == "None":
            return

        unload_payload = {
            "model": self.model_name,
            "prompt": "",
            "stream": False,
            "keep_alive": 0,
        }

        try:
            data = json.dumps(
                unload_payload,
                ensure_ascii=False,
            ).encode("utf-8")

            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=data,
                headers={
                    "Content-Type": "application/json"
                },
                method="POST",
            )

            with urllib.request.urlopen(
                req,
                timeout=10,
            ) as response:

                if response.status == 200:
                    print(
                        "[AI-RUNTIME] Ollama model unloaded "
                        "from runtime memory."
                    )

        except urllib.error.URLError as e:
            print(
                "[AI-RUNTIME] Ollama unload request failed: "
                f"{e}"
            )

        except Exception as e:
            print(
                "[AI-RUNTIME] Ollama unload exception: "
                f"{e}"
            )

    # ==================================================================
    # OLLAMA RUNTIME STEP COMPLETION
    # ======================================================================

    def _build_step_completion(
        self,
        completion=None,
    ) -> dict:
        """
        Builds the provider-specific completion instruction
        used by the Ollama cognitive runtime.

        This belongs to Ollama rather than AIBase because the
        completion message is part of Ollama's own runtime
        sequencing.

        GameBridge action receipts, such as:

            {"status": "dispatched"}

        are passed to Ollama separately as actual tool receipts.
        """

        if completion is None:
            completion = {
                "status": "completed"
            }

        return completion

    # ==================================================================
    # OLLAMA TOOL TRANSLATION
    # ==================================================================

    def _build_ollama_tools(
        self,
        context=None,
    ) -> list:
        """
        Translates GameBridge semantic tool definitions into
        Ollama's native tool schema.

        GameBridge owns what the tools mean.
        Ollama owns how those tools are represented to Ollama.
        """

        gamebridge_tools = self.get_gamebridge_tools(
            context
        )
        ollama_tools = []

        for tool in gamebridge_tools:

            if not isinstance(tool, dict):
                continue

            name = tool.get("name")

            if not name:
                continue

            ollama_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": tool.get(
                            "description",
                            "",
                        ),
                        "parameters": tool.get(
                            "parameters",
                            {
                                "type": "object",
                                "additionalProperties": True,
                            },
                        ),
                    },
                }
            )

        return ollama_tools

    # ==================================================================
    # RUNTIME COMPLETION
    # ==================================================================

    def continue_runtime(
        self,
        completion=None,
        telemetry_data=None,
    ) -> str:

        if not self.runtime_active:
            return ""

        # --------------------------------------------------------------
        # UPDATE TELEMETRY IF GAMEBRIDGE RETURNED NEW DATA
        # --------------------------------------------------------------

        if telemetry_data is not None:

            self.runtime_context[
                "telemetry_data"
            ] = telemetry_data

        # --------------------------------------------------------------
        # TOOL CALL COMPLETION
        # --------------------------------------------------------------

        if self.runtime_last_tool_call_id:

            if completion is None:
                return ""

            self.runtime_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": (
                        self.runtime_last_tool_call_id
                    ),
                    "content": json.dumps(
                        completion,
                        ensure_ascii=False,
                    ),
                }
            )

            self.runtime_last_tool_call_id = None

        # --------------------------------------------------------------
        # OLLAMA STEP COMPLETION
        # --------------------------------------------------------------

        elif completion is not None:

            step_completion = (
                self._build_step_completion(
                    completion
                )
            )

            self.runtime_messages.append(
                {
                    "role": "user",
                    "content": (
                        "[GAMEBRIDGE STEP COMPLETED]\n"
                        f"{json.dumps(step_completion, ensure_ascii=False)}"
                    ),
                }
            )

            if self.runtime_last_step_type == "channel1":

                self.stop_runtime()

                return ""

        # --------------------------------------------------------------
        # CONTINUE SAME COGNITIVE RUNTIME
        # --------------------------------------------------------------

        return self._request_runtime_step()

    # ==================================================================
    # RUNTIME REQUEST
    # ==================================================================

    def _request_runtime_step(self) -> str:

        # --------------------------------------------------------------
        # REFRESH LIVE GAMEBRIDGE RUNTIME STATE
        # --------------------------------------------------------------

        context = dict(
            self.runtime_context
        )

        if self.runtime_state_callback is not None:
            try:
                live_state = self.runtime_state_callback()

                if isinstance(live_state, dict):
                    context.update(
                        live_state
                    )

            except Exception:
                pass

        # --------------------------------------------------------------
        # TEMPORARY DEBUG
        # --------------------------------------------------------------

        print(
            "[DEBUG-RUNTIME-CONTEXT]",
            context
        )

        k2_adapter = context.get(
            "channel2_adapter_active",
            False,
        )

        tools = self._build_ollama_tools(
            context
        )

        print(
            "[DEBUG-RUNTIME-TOOLS]",
            [
                tool.get("function", {}).get("name")
                for tool in tools
                if isinstance(tool, dict)
            ]
        )

        payload = {
            "model": self.model_name,
            "messages": self.runtime_messages,
            "stream": False,
            "options": {
                "temperature": (
                    0.1
                    if k2_adapter
                    else 0.3
                )
            },
        }

        if tools:
            payload["tools"] = tools

        try:

            data = json.dumps(
                payload,
                ensure_ascii=False,
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

                message = response_data.get(
                    "message",
                    {},
                )

                # ------------------------------------------------------
                # STORE OLLAMA MESSAGE
                # ------------------------------------------------------

                self.runtime_messages.append(
                    message
                )

                tool_calls = message.get(
                    "tool_calls",
                    [],
                )

                # ------------------------------------------------------
                # TOOL STEP
                # ------------------------------------------------------

                if tool_calls:

                    tool_call = tool_calls[0]

                    function_data = tool_call.get(
                        "function",
                        {},
                    )

                    function_name = function_data.get(
                        "name",
                        "",
                    )

                    arguments = function_data.get(
                        "arguments",
                        {},
                    )

                    if isinstance(arguments, str):

                        try:
                            arguments = json.loads(
                                arguments
                            )

                        except json.JSONDecodeError:
                            arguments = {}

                    tool_call_id = tool_call.get(
                        "id"
                    )

                    # --------------------------------------------------
                    # GAMEBRIDGE TIME
                    # --------------------------------------------------

                    if (
                        function_name
                        == self.TOOL_TIME
                    ):

                        print(
                            "[AI-RUNTIME] OS date/time requested "
                            "by cognitive runtime."
                        )

                        try:

                            time_data = (
                                self.execute_gamebridge_tool(
                                    function_name,
                                    arguments,
                                )
                            )

                        except Exception as e:

                            print(
                                "[AI-RUNTIME] OS date/time request "
                                f"failed: {e}"
                            )

                            time_data = {
                                "status": "unavailable"
                            }

                        self.runtime_messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps(
                                    time_data,
                                    ensure_ascii=False,
                                ),
                            }
                        )

                        self.runtime_last_tool_call_id = None
                        self.runtime_last_step_type = (
                            "time"
                        )

                        return self._request_runtime_step()

                    # --------------------------------------------------
                    # GAMEBRIDGE TELEMETRY
                    # --------------------------------------------------

                    if (
                        function_name
                        == self.TOOL_TELEMETRY
                    ):

                        print(
                            "[AI-RUNTIME] Telemetry requested "
                            "by cognitive runtime."
                        )

                        self.runtime_last_tool_call_id = (
                            tool_call_id
                        )

                        self.runtime_last_step_type = (
                            "telemetry"
                        )

                        return json.dumps(
                            {
                                "tool": self.TOOL_TELEMETRY,
                                "arguments": arguments,
                            },
                            ensure_ascii=False,
                        )

                    # --------------------------------------------------
                    # CHANNEL 2 / APPLICATION TOOL
                    # --------------------------------------------------

                    if (
                        function_name
                        == self.TOOL_ACTION
                    ):

                        self.runtime_last_tool_call_id = (
                            tool_call_id
                        )

                        self.runtime_last_step_type = (
                            "channel2"
                        )

                        return json.dumps(
                            arguments,
                            ensure_ascii=False,
                        )

                    # --------------------------------------------------
                    # UNKNOWN GAMEBRIDGE TOOL
                    # --------------------------------------------------

                    unknown_tool_result = {
                        "status": "unknown_tool",
                        "tool": function_name,
                    }

                    self.runtime_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": json.dumps(
                                unknown_tool_result,
                                ensure_ascii=False,
                            ),
                        }
                    )

                    self.runtime_last_tool_call_id = None
                    self.runtime_last_step_type = (
                        "unknown_tool"
                    )

                    return self._request_runtime_step()

                # ------------------------------------------------------
                # CHANNEL 1 / HUMAN STEP
                # ------------------------------------------------------

                content = message.get(
                    "content",
                    "",
                ).strip()

                self.runtime_last_step_type = (
                    "channel1"
                )

                return content

        except urllib.error.URLError as e:

            print(
                "[AI-API-ERROR] Communications block failed "
                "to resolve Ollama loopback endpoint: "
                f"{e}"
            )

            self.stop_runtime()

            return (
                "[AI-API-ERROR] Local Ollama instances "
                "are currently unresponsive."
            )

        except Exception as e:

            print(
                "[AI-API-ERROR] Critical execution exception: "
                f"{e}"
            )

            self.stop_runtime()

            return (
                "[AI-API-ERROR] Internal system AI client "
                "exception."
            )

    # ==================================================================
    # GENERATE RESPONSE
    # ==================================================================

    def generate_response(
        self,
        context: dict,
        adapter_folder: str = "None",
    ) -> str:

        if not self.model_name or self.model_name == "None":
            return "[AI-DISABLED] No Ollama model selected."

        # --------------------------------------------------------------
        # PROMPT SOURCES
        # --------------------------------------------------------------

        gamebridge_prompt = (
            self._load_gamebridge_system_prompt()
        )

        plugin_prompt = (
            self._load_plugin_prompt(
                adapter_folder
            )
        )

        full_system_prompt = (
            self.build_gamebridge_system_prompt(
                gamebridge_prompt,
                plugin_prompt,
                context,
            )
        )

        # --------------------------------------------------------------
        # START NEW COGNITIVE RUNTIME
        # --------------------------------------------------------------

        self._start_runtime(
            context,
            adapter_folder,
            full_system_prompt,
        )

        # --------------------------------------------------------------
        # REQUEST FIRST COGNITIVE STEP
        # --------------------------------------------------------------

        return self._request_runtime_step()