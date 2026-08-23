AIDE PROJECT PACKAGE
====================

PROJECT:
gamebridge_v1

SOURCE ROOTS:
C:/Users/joel/Desktop/Ny mapp/gamebridge_v1

FILES:
31

==================================================
FILE: adapters/adapter_loader.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
CONNECTIONS:
  - FETCHES FROM: adapters/base_adapter.py (Interface blueprint), core/path_core.py
  - CALLED BY: functions/bridge_functions.py
"""

import os
import importlib
import sys
from core.path_core import PathCore

class AdapterLoader:
    def __init__(self, plugin_dir: str = None):
        # FIXED: Relies strictly on the global centralized PathCore if no folder allocation is passed
        if plugin_dir is None:
            self.plugin_dir = PathCore.get_adapter_root()
        else:
            self.plugin_dir = plugin_dir

    def discover_and_load(self) -> dict:
        """Scans subdirectories and registers valid adapters dynamically using global system paths."""
        available_adapters = {}
        
        if not os.path.exists(self.plugin_dir):
            print(f"[LOADER-WARNING] Execution block aborted: Target path does not exist: {self.plugin_dir}")
            return available_adapters

        # Ensure the adapters root directory is officially registered in Python's core search vector
        if self.plugin_dir not in sys.path:
            sys.path.insert(0, self.plugin_dir)

        for folder in os.listdir(self.plugin_dir):
            folder_path = os.path.join(self.plugin_dir, folder)
            
            # Skip hidden directories, caches, or python package configurations
            if not os.path.isdir(folder_path) or folder.startswith("__") or folder.startswith("."):
                continue
                
            main_file = os.path.join(folder_path, "main_adapter.py")
            if not os.path.exists(main_file):
                continue

            try:
                # FIXED: Shifted from absolute hardcoded 'src.adapters' package strings to context-free imports
                # Python now scans folder subdirectories cleanly because self.plugin_dir is injected in sys.path
                module_path = f"{folder}.main_adapter"
                
                # Force reload or clean import to avoid stale tracking references in memory
                if module_path in sys.modules:
                    importlib.reload(sys.modules[module_path])
                module = importlib.import_module(module_path)
                
                # Scan module attributes for a class inheriting from BaseAdapter
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    
                    if isinstance(attribute, type) and attribute_name != "BaseAdapter" and "Adapter" in attribute_name:
                        # Instantiate temporarily to extract the exposed display name
                        temp_instance = attribute()
                        display_name = getattr(temp_instance, "adapter_name", folder)
                        
                        # Safely invoke shutdown on the temp instance if initialized to prevent background memory leaks
                        if hasattr(temp_instance, "shutdown"):
                            try:
                                temp_instance.shutdown()
                            except Exception:
                                pass
                        
                        available_adapters[display_name] = attribute
                        print(f"[LOADER] Discovered and registered extension: '{display_name}' from global tree folder {folder}/")
                        
            except Exception as e:
                print(f"[LOADER-ERROR] Failed to load extension in directory '{folder}': {e}")

        return available_adapters


```

==================================================
FILE: adapters/base_adapter.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
CONNECTIONS:
  - FETCHES FROM: core/path_core.py (Absolute layout vectors)
  - CALLED BY: Dynamic core extensions and concrete adapter implementations.
"""

from abc import ABC, abstractmethod
from typing import Any
from core.path_core import PathCore

class BaseAdapter(ABC):
    def __init__(self):
        # Exposed publicly for core loader registration
        self.adapter_name = "BaseInterface"
        
        # FIXED: Core path vectors are now pulled internally to allow seamless migration
        self.project_root = PathCore.PROJECT_ROOT
        self.adapters_root = PathCore.get_adapter_root()
        
    @abstractmethod
    def initialize(self):
        """Initializes internal variables and loads localized plugin configurations."""
        pass

    @abstractmethod
    def boot_or_attach(self):
        """Asynchronously launches or attaches to the destination target application environment."""
        pass

    @abstractmethod
    def get_capabilities(self) -> dict:
        """
        Returns the plugin's unique passive or active execution capabilities.
        Uses a fluid dictionary structure to prevent hardcoding assumptions in the kernel.
        """
        pass

    @abstractmethod
    def read_telemetry(self) -> dict:
        """Reads and extracts the destination target application's current state matrix as a dict."""
        pass

    @abstractmethod
    def execute_interaction(self, action_data: Any):
        """
        Executes transaction strings, raw inputs, or command payloads against target environments.
        Supports clean JSON strings, pre-parsed dictionaries, or complex execution envelopes.
        """
        pass

    @abstractmethod
    def shutdown(self):
        """Gracefully detaches connections from targets and flushes assigned resources clean."""
        pass


```

==================================================
FILE: ai/internet_transport.py
TYPE: Kod
==================================================

```python
# -*- coding: utf-8 -*-
"""
GameBridge Internet Transport

KOPPLINGAR:
 - HÄMTAR FRÅN:
     - core.path_core.PathCore
     - providers.tavily_provider.TavilyProvider
 - ANROPAS AV:
     - core.cognitive_router_core

ANSVAR:
 - GameBridges befintliga internet-accesspunkt.
 - Ta emot router-context.
 - Extrahera user_input som sökfråga.
 - Anropa vald internet-provider.
 - Omvandla provider-resultatet till GameBridges befintliga
   JSON-envelope för Channel 1.
 - Returnera ett rent "response"-fält som den befintliga
   routerns JSON-tvätt kan extrahera.
 - Hantera providerfel utan att fabricera internetdata.

ARKITEKTUR:

    cognitive_router_core
            |
            v
    InternetTransport
            |
            v
    TavilyProvider
            |
            v
       Tavily API

VIKTIGT:
 - InternetTransport är den enda internet-accesspunkten
   som cognitive_router_core behöver känna till.
 - TavilyProvider innehåller provider-specifik logik.
 - Rått provider-JSON skickas ALDRIG direkt till Channel 1.
 - InternetTransport återställer GameBridges tidigare
   {"response": "...", "link": "..."}-kontrakt.
"""

import json
import os
from datetime import datetime, timezone

from core.path_core import PathCore
from providers.tavily_provider import TavilyProvider


class InternetTransport:
    """
    GameBridges stabila internet-accesspunkt.

    Routern behöver inte känna till vilken provider
    som används under transportlagret.
    """

    def __init__(self, provider=None, timeout=8.0):
        self.timeout = float(timeout)

        # Provider kan injiceras för tester eller framtida providers.
        self.provider = provider or TavilyProvider(
            timeout=self.timeout
        )

        self.enabled = True

        self.log_path = PathCore.get_internet_log_path()

    def set_enabled(self, enabled: bool) -> None:
        """Aktiverar eller stänger av extern internetåtkomst."""
        self.enabled = bool(enabled)

    def is_enabled(self) -> bool:
        """Returnerar aktuell internetstatus."""
        return self.enabled

    def send_cognitive_request(self, context: dict) -> str:
        """
        Befintligt anropskontrakt mot cognitive_router_core.

        context["user_input"] används som faktisk sökfråga.

        Provider-resultatet konverteras till GameBridges
        äldre response/link-envelope så att routerns befintliga
        JSON-tvätt kan extrahera endast det mänskliga svaret.

        Returnerar:

            {
                "response": "...",
                "link": "..."
            }
        """

        if not isinstance(context, dict):
            return self._response(
                response="Ogiltig cognitive context.",
                link=""
            )

        query = str(
            context.get("user_input", "")
        ).strip()

        if not query:
            return self._response(
                response="Ingen sökfråga angiven.",
                link=""
            )

        if not self.enabled:
            return self._response(
                response="Internetåtkomst är avstängd.",
                link=""
            )

        print(
            f"[+] [INTERNET_TRANSPORT] "
            f"Extern sökning: '{query}'"
        )

        try:
            # --------------------------------------------------------------
            # Provider-anrop
            # --------------------------------------------------------------

            result = self.provider.search(query)

            if not isinstance(result, dict):
                failure = {
                    "success": False,
                    "provider": getattr(
                        self.provider,
                        "name",
                        "unknown"
                    ),
                    "query": query,
                    "results": [],
                    "error": "Providern returnerade ett ogiltigt resultat."
                }

                self._log_query(
                    query=query,
                    context=context,
                    result=failure
                )

                return self._response(
                    response=(
                        "[API-ERROR] Internetprovidern "
                        "returnerade ett ogiltigt resultat."
                    ),
                    link=""
                )

            self._log_query(
                query=query,
                context=context,
                result=result
            )

            # --------------------------------------------------------------
            # Providerfel
            # --------------------------------------------------------------

            if not result.get("success", False):
                provider_error = result.get(
                    "error",
                    "Okänt providerfel."
                )

                return self._response(
                    response=(
                        f"[API-ERROR] Internetåtkomst misslyckades: "
                        f"{provider_error}"
                    ),
                    link=""
                )

            # --------------------------------------------------------------
            # Hämta resultat
            # --------------------------------------------------------------

            results = result.get(
                "results",
                []
            )

            if not isinstance(results, list):
                results = []

            if not results:
                fallback_link = (
                    "https://duckduckgo.com/?q="
                    + self._quote_query(query)
                )

                return self._response(
                    response=(
                        f"Inga aktuella internetresultat hittades "
                        f"för '{query}'."
                    ),
                    link=fallback_link
                )

            # --------------------------------------------------------------
            # Bygg rent mänskligt svar
            #
            # Detta är den viktiga kompatibilitetsdelen.
            #
            # Rått provider-JSON:
            #
            #   {"success": true, "results": [...]}
            #
            # får ALDRIG lämna transportlagret.
            #
            # I stället skapas samma envelope som den gamla
            # fungerande transporten använde:
            #
            #   {"response": "...", "link": "..."}
            # --------------------------------------------------------------

            response_parts = [
                f"Här är aktuell information om '{query}':"
            ]

            first_link = ""

            for idx, item in enumerate(
                results[:3],
                start=1
            ):
                if not isinstance(item, dict):
                    continue

                title = (
                    item.get("title")
                    or "Källa"
                )

                content = (
                    item.get("content")
                    or item.get("snippet")
                    or ""
                )

                url = (
                    item.get("url")
                    or ""
                )

                if not first_link and url:
                    first_link = url

                response_parts.append(
                    f"[{idx}] {title}\n"
                    f"{content}\n"
                    f"Källa: {url}"
                )

            constructed_response = "\n\n".join(
                response_parts
            )

            return self._response(
                response=constructed_response,
                link=first_link
            )

        except Exception as exc:
            error = (
                f"{type(exc).__name__}: {exc}"
            )

            print(
                f"[-] [INTERNET_TRANSPORT] "
                f"{error}"
            )

            failure = {
                "success": False,
                "provider": getattr(
                    self.provider,
                    "name",
                    "unknown"
                ),
                "query": query,
                "results": [],
                "error": error
            }

            self._log_query(
                query=query,
                context=context,
                result=failure
            )

            return self._response(
                response=(
                    "[API-ERROR] Kunde inte hämta "
                    "realtidsdata från internet."
                ),
                link=""
            )

    @staticmethod
    def _quote_query(query: str) -> str:
        """
        Minimal URL-encoding utan att lägga till ytterligare
        beroenden eller ändra provider-kontraktet.
        """
        from urllib.parse import quote

        return quote(
            query,
            safe=""
        )

    def _response(
        self,
        response: str,
        link: str = ""
    ) -> str:
        """
        GameBridges befintliga externa AI-envelope.

        cognitive_router_core känner redan igen "response"
        och extraherar detta fält innan Channel 1.

        Rå providerdata exponeras därför inte.
        """

        return json.dumps(
            {
                "response": response,
                "link": link
            },
            ensure_ascii=False
        )

    def _log_query(
        self,
        query: str,
        context: dict,
        result: dict
    ) -> None:
        """
        Append-only-logg för faktiska sökförsök.

        API-nyckel och sökresultatens fulltext sparas inte.
        """

        try:
            os.makedirs(
                os.path.dirname(self.log_path),
                exist_ok=True
            )

            results = result.get(
                "results",
                []
            )

            if not isinstance(results, list):
                results = []

            record = {
                "timestamp": (
                    datetime.now(timezone.utc)
                    .astimezone()
                    .isoformat()
                ),
                "session_id": context.get(
                    "session_id",
                    "default"
                ),
                "query": query,
                "provider": result.get(
                    "provider",
                    getattr(
                        self.provider,
                        "name",
                        "unknown"
                    )
                ),
                "success": bool(
                    result.get(
                        "success",
                        False
                    )
                ),
                "result_count": len(
                    results
                ),
                "error": result.get(
                    "error"
                )
            }

            with open(
                self.log_path,
                "a",
                encoding="utf-8"
            ) as logfile:
                logfile.write(
                    json.dumps(
                        record,
                        ensure_ascii=False
                    ) + "\n"
                )

        except Exception as exc:
            # Loggfel får aldrig slå sönder
            # själva internettransporten.
            print(
                f"[!] [INTERNET_TRANSPORT] "
                f"Kunde inte skriva söklogg: {exc}"
            )

```

==================================================
FILE: ai/ollama_client.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
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
    def __init__(self, model_name: str = "sailwind-pilot", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self.show_url = f"{base_url}/api/show"
        
    def check_model_status(self) -> str:
        """Queries the local Ollama instance to track current model availability states."""
        payload = {"name": self.model_name}
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(self.show_url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    return "READY"
        except urllib.error.URLError:
            return "OFFLINE"
        except Exception:
            return "LOADING"
        return "OFFLINE"
        
    def _load_adapter_system_prompt(self, adapter_folder: str) -> str:
        """Reads the extension's system_prompt.txt dynamically from disk using relative paths."""
        if not adapter_folder or adapter_folder == "None":
            return "You are the G.A.M.E. B.R.I.D.G.E. AI framework. No extension target is currently active."
            
        prompt_path = os.path.join("plugins", adapter_folder, "system_prompt.txt")
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                print(f"[AI-ERROR] Failed to load local system prompt vector from '{prompt_path}': {e}")
                
        return "You are an AI integrated via G.A.M.E. B.R.I.D.G.E. Act as a generalized runtime assistant."

    def generate_response(self, context: dict, adapter_folder: str = "None") -> str:
        """Evaluates token contexts across Channel 1 and Channel 2 dispatch guidelines with forced JSON boundaries."""
        user_input = context.get("user_input", "")
        telemetry = context.get("telemetry_data", {})
        capabilities = context.get("capabilities", {})
        
        base_system_prompt = self._load_adapter_system_prompt(adapter_folder)
        k1_chat = context.get("channel1_chat_active", False)
        k2_adapter = context.get("channel2_adapter_active", False)
        
        channel_instructions = "\n\n[ACTIVE INTERACTION PROFILE STATE]\n"
        if k1_chat and k2_adapter:
            channel_instructions += "Channel 1 (Dialogue Chat) and Channel 2 (Target App Adapter) are active. Engage in human dialogue and execute requested environmental interactions concurrently. You MUST return your answer inside a valid JSON object structure."
        elif k1_chat and not k2_adapter:
            channel_instructions += "Channel 1 (Dialogue Chat) is active. Channel 2 (Target App Adapter) is locked. Pure conversational dialogue state. Do not emit machine execution codes or interface modifications."
        elif not k1_chat and k2_adapter:
            channel_instructions += "Channel 1 (Dialogue Chat) is locked. Channel 2 (Target App Adapter) is active. Focus entirely on automated app interactions. Respond with short, raw execution payload text decisions only."
        else:
            channel_instructions += "All routing vectors suspended."

        full_system_prompt = (
            f"{base_system_prompt}{channel_instructions}\n\n"
            f"Available extension capabilities matrix:\n{json.dumps(capabilities, indent=2)}\n\n"
            f"Active telemetry data streams from destination context:\n{json.dumps(telemetry, indent=2)}"
        )

        # Enforce highly deterministic responses when adapter manipulation is active
        target_temp = 0.1 if k2_adapter else 0.3
        
        payload = {
            "model": self.model_name,
            "prompt": user_input,
            "system": full_system_prompt,
            "stream": False,
            "options": {
                "temperature": target_temp
            }
        }
        
        # Hardcoded grammar barrier lock via Ollama native API parameter
        if k2_adapter:
            payload["format"] = "json"
        
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(self.api_url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=90) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                return response_data.get("response", "").strip()
        except urllib.error.URLError as e:
            print(f"[AI-API-ERROR] Communications block failed to resolve Ollama loopback endpoint: {e}")
            return "[AI-API-ERROR] Local Ollama instances are currently unresponsive."
        except Exception as e:
            print(f"[AI-API-ERROR] Critical execution exception: {e}")
            return "[AI-API-ERROR] Internal system AI client exception."


```

==================================================
FILE: config/locales.json
TYPE: Konfiguration/Data
==================================================

```json
{
    "en": {
        "title": "G.A.M.E. B.R.I.D.G.E. - Control Panel",
        "status_ready": "Status: Ready",
        "status_processing": "Status: Processing...",
        "ai_toggle": "AI Active",
        "internet_toggle": "Internet AI",
        "topmost_toggle": "Stay on Top",
        "boot_btn": "Launch / Attach App",
        "disconnect_btn": "Disconnect",
        "no_adapter": "No Adapter Loaded",
        "matrix_title": "CHANNEL AND SIGNAL MATRIX CONTROL",
        "chat_switch": "Text Chat (Channel 1)",
        "voice_label": "Voice Mode:",
        "voice_modes": ["OFF", "PTT", "LISTEN"],
        "telemetry_switch": "Read Telemetry (Fetch Data)",
        "write_switch": "Write to Adapter (Channel 2)",
        "log_ready": "=== G.A.M.E. B.R.I.D.G.E. INTERFACE READY ===\n",
        "input_placeholder": "Type message to Channel 1 here...",
        "send_btn": "Send",
        "lock_switch": "Lock keyboard input (Safe Voice Mode)",
        "hotkey_btn": "Set adapter voice hotkey",
        "hotkey_wait": "Press desired key...",
        "log_tel_on": "Telemetry gathering ENABLED.",
        "log_tel_off": "Telemetry gathering DISABLED.",
        "log_ai_on": "AI infrastructure DEPLOYED.",
        "log_ai_off": "AI infrastructure SUSPENDED."
    },
    "sv": {
        "title": "G.A.M.E. B.R.I.D.G.E. - Kontrollpanel",
        "status_ready": "Status: Redo",
        "status_processing": "Status: Processar...",
        "ai_toggle": "AI Aktiv",
        "internet_toggle": "Internet AI",
        "topmost_toggle": "Alltid överst",
        "boot_btn": "Starta / Anslut Målapp",
        "disconnect_btn": "Koppla ifrån",
        "no_adapter": "Ingen Adapter Laddad",
        "matrix_title": "KANAL- OCH SIGNALKONTROLL",
        "chat_switch": "Textchatt (Kanal 1)",
        "voice_label": "Röstläge:",
        "voice_modes": ["AV", "PTT", "LYSSNA"],
        "telemetry_switch": "Läs Telemetri (Hämta data)",
        "write_switch": "Skriv till Adapter (Kanal 2)",
        "log_ready": "=== G.A.M.E. B.R.I.D.G.E. GRÄNSSNITT REDO ===\n",
        "input_placeholder": "Skriv meddelande till Kanal 1 här...",
        "send_btn": "Skicka",
        "lock_switch": "Lås tangentbordsinmatning (Säkert röstläge)",
        "hotkey_btn": "Sätt röstknapp för adapter",
        "hotkey_wait": "Tryck på önskad knapp...",
        "log_tel_on": "Telemetriläsning AKTIVERAD.",
        "log_tel_off": "Telemetriläsning DEAKTIVERAD.",
        "log_ai_on": "AI-infrastruktur AKTIVERAD.",
        "log_ai_off": "AI-infrastruktur AVSTÄNGD."
    }
}

```

==================================================
FILE: config/settings.json
TYPE: Konfiguration/Data
==================================================

```json
{
    "ai_model_name": "sailwind-pilot:latest",
    "voice_hotkey": "f12"
}

```

==================================================
FILE: core/channel_matrix.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
 - HÄMTAR FRÅN: Isolerade kärntillstånd (Inga externa logikberoenden).
 - ANROPAS AV: main.py, functions/bridge_function.py, functions/router_functions.py, interface/client_gui.py
"""

import threading

class ChannelMatrix:
    def __init__(self):
        # Thread synchronization lock for concurrent matrix evaluation
        self._lock = threading.Lock()
        
        # Synced identification properties across GUI and Bridge Core
        self.channel1_chat_active = False     # Channel 1: Chat / Dialogue
        self.channel2_adapter_active = False  # Channel 2: Target App Interaction
        self.ai_generation_enabled = False    # Master switch for local LLM evaluations
        
        # EXPANSION v3.0: Explicit user-controlled capability for Internet AI (Opt-in)
        self.internet_ai_enabled = False

    def update_states(self, ch1_chat: bool, ch2_adapter: bool, ai_active: bool, internet_active: bool = False) -> None:
        """Transactionally updates the state matrix values from the GUI layer."""
        with self._lock:
            self.channel1_chat_active = ch1_chat
            self.channel2_adapter_active = ch2_adapter
            self.ai_generation_enabled = ai_active
            self.internet_ai_enabled = internet_active
            print(f"[MATRIX-SYNC] States committed -> Ch1: {ch1_chat}, Ch2: {ch2_adapter}, AI Active: {ai_active}, Internet AI: {internet_active}")

    def is_ai_blocked(self) -> bool:
        """Enforces a strict safety barrier check before allowing any LLM inference tokens."""
        with self._lock:
            return not self.ai_generation_enabled

    def is_internet_blocked(self) -> bool:
        """Enforces a strict capability barrier check before allowing external port 8080 routing."""
        with self._lock:
            return not self.internet_ai_enabled

    def should_route_to_chat(self) -> bool:
        """Validates if the computed AI response text is authorized to render in the GUI."""
        with self._lock:
            return self.channel1_chat_active

    def should_route_to_adapter(self, active_instance) -> bool:
        """Validates if automated AI payload dispatches are allowed to mutate the target app."""
        with self._lock:
            return self.channel2_adapter_active and active_instance is not None

```

==================================================
FILE: core/cognitive_router_core.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
 - HÄMTAR FRÅN: ai/ollama_client.py, core/io_layer.py, core/channel_matrix.py, functions/router_functions.py
 - ANROPAS AV: functions/bridge_functions.py

"""

import threading
from functions.router_functions import function_pipeline_worker

class CognitiveRouterCore:
    def __init__(self, ai_client=None, matrix=None, io_layer=None, core_parent=None):
        self.ai_client = ai_client
        self.matrix = matrix
        self.io_layer = io_layer
        self.core_parent = core_parent  # Context binding to extract live capability toggles (e.g. internet_ai_enabled)

    def route_transactional_flow(self, user_text: str, active_adapter, adapter_folder: str, gui_log_callback, ui_status_callback, speech_callback) -> None:
        """Asynchronously dispatches token evaluation to the functional backend to keep UI metrics completely fluid."""
        threading.Thread(
            target=function_pipeline_worker,
            args=(self, user_text, active_adapter, adapter_folder, gui_log_callback, ui_status_callback, speech_callback),
            daemon=True
        ).start()

```

==================================================
FILE: core/config_core.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: core/path_core.py
 - CALLED BY: functions/bridge_functions.py, core/cognitive_router_core.py

"""

import json
import os
import threading
from core.path_core import PathCore

class ConfigCore:
    def __init__(self):
        self._lock = threading.Lock()
        self.config_path = PathCore.get_config_path("settings.json")

    def load_global_config(self) -> dict:
        """Resolves system master configuration directories and schemas transactionally."""
        default_config = {"ai_model_name": "sailwind-pilot", "voice_hotkey": "f12"}
        config_dir = os.path.dirname(self.config_path)
        
        with self._lock:
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                        if "voice_hotkey" not in config_data:
                            config_data["voice_hotkey"] = "f12"
                        return config_data
                except Exception:
                    pass
            
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=4)
            except Exception:
                pass
            return default_config

    def save_global_config(self, config_data: dict) -> None:
        """Persists engine configurations safely back to the global disk matrix."""
        with self._lock:
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=4)
            except Exception as e:
                print(f"[CONFIG-ERROR] Failed to save global configuration: {e}")

    def save_adapter_hotkey(self, adapter_folder: str, hotkey: str) -> None:
        """Safely injects and persists a local hotkey bind into a specific plugin manifest."""
        if not adapter_folder or adapter_folder == "None":
            return
            
        config_file = PathCore.get_adapter_file(adapter_folder, "plugin_config.json")
        plugin_data = {}
        
        with self._lock:
            if os.path.exists(config_file):
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        plugin_data = json.load(f)
                except Exception:
                    pass
                    
            plugin_data["voice_hotkey"] = hotkey
            try:
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(plugin_data, f, indent=4)
            except Exception as e:
                print(f"[CONFIG-ERROR] Failed to save adapter configuration: {e}")


```

==================================================
FILE: core/hotkey_capture_core.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: interface/hardware_io.py
 - CALLED BY: functions/bridge_functions.py

"""

import threading
import keyboard

class HotkeyCaptureCore:
    def __init__(self, hardware_subsystem):
        self.hardware = hardware_subsystem
        self._lock = threading.Lock()

    def capture_next_keypress(self, before_callback, success_callback, final_callback) -> None:
        """Asynchronously intercepts the next keyboard raw event to rebind peripheral triggers."""
        def worker():
            try:
                before_callback()
                recorded_key = keyboard.read_key(suppress=True)
                cleaned_key = self.hardware.normalize_key(recorded_key) if self.hardware else recorded_key
                success_callback(cleaned_key)
            except Exception as e:
                print(f"[HOTKEY-CAPTURE-ERROR] Dynamic key recording faulted: {e}")
            finally:
                final_callback()

        threading.Thread(target=worker, daemon=True).start()


```

==================================================
FILE: core/io_layer.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
CONNECTIONS:
- FETCHES FROM: Isolated core routing (No external application dependencies).
- CALLED BY: main.py, core/channel_matrix.py, functions/router_functions.py
"""

import threading
from typing import Any, Callable, Optional

class GameBridgeIOLayer:
    def __init__(self):
        # Thread synchronization vectors for async stream safety
        self._routing_lock = threading.Lock()

        # Channel 1: Conversation links (Registered by GUI or Core)
        self._ui_log_callback: Optional[Callable[[str, str], None]] = None

        # Channel 2: Interaction links (Registered dynamically by active adapters)
        self._target_input_callback: Optional[Callable[[Any], None]] = None
        self._target_output_callback: Optional[Callable[[], Any]] = None
        
        # MONITORING: Callback vector for routing raw telemetry and payloads to GUI
        self._monitor_callback: Optional[Callable[[str], None]] = None

    # === CHANNEL 1: CONVERSATION (User <-> AI Dialogue) ===
    def register_ui_channel(self, log_cb: Callable[[str, str], None]) -> None:
        """Links the presentation layer's log box directly to Channel 1."""
        with self._routing_lock:
            self._ui_log_callback = log_cb
            print("[IO-LAYER] Channel 1: GUI conversation channel successfully registered.")

    def send_to_kanal_1(self, sender: str, message: str) -> None:
        """Routes human or AI text messages safely to the conversation log view."""
        with self._routing_lock:
            callback = self._ui_log_callback

            if callback:
                callback(sender, message)
            else:
                print(f"[IO-LAYER] Channel 1 [From: {sender}]: {message}")

    # === CHANNEL 2: INTERACTION (AI <-> Bridge <-> Active Adapter Input) ===
    def register_adapter_channels(self, input_cb: Callable[[Any], None], output_cb: Callable[[], Any]) -> None:
        """Links the active adapter's generic input and output methods straight to Channel 2."""
        with self._routing_lock:
            self._target_input_callback = input_cb
            self._target_output_callback = output_cb
            print("[IO-LAYER] Channel 2: Adapter data matrix interface successfully registered.")

    def send_to_kanal_2(self, payload: Any) -> None:
        """Relays cognitive action payloads or tokens directly to the active app adapter interface."""
        with self._routing_lock:
            callback = self._target_input_callback

            if callback:
                # Invoked safely via transaction routing boundaries
                callback(payload)
            else:
                print("[IO-LAYER] Channel 2 Aborted: No active target app receiver allocated.")

    def read_from_kanal_2(self) -> Any:
        """Fetches the current live state matrix or telemetry metrics from the active adapter layer."""
        with self._routing_lock:
            callback = self._target_output_callback

            if callback:
                return callback()
            return None

    # === EXPANSION v3.5: MONITOR CHANNELS (Real-time telemetry and payload tracing) ===
    def register_monitor_channel(self, monitor_cb: Callable[[str], None]) -> None:
        """Links the green diagnostic terminal in the GUI directly to diagnostic emitters."""
        with self._routing_lock:
            self._monitor_callback = monitor_cb
            print("[IO-LAYER] Monitor Channel: Diagnostic monitoring core vector successfully bound.")

    def send_to_monitor(self, message: str) -> None:
        """Transactionally pushes structural diagnostics or telemetry logs straight to the monitor window."""
        with self._routing_lock:
            callback = self._monitor_callback
            
            if callback:
                callback(message)

```

==================================================
FILE: core/localization_core.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
import locale
import os
import json
import threading
import sys
from typing import Dict, Any
from core.path_core import PathCore

class LocalizationCore:
    def __init__(self):
        self._lock = threading.Lock()
        self.config_path = PathCore.get_config_path("settings.json")
        self.locales_path = PathCore.get_config_path("locales.json")
        
        self.system_lang = "en" # Global fallback
        self._matrices: Dict[str, Dict[str, Any]] = {}
        
        # Hårdkodad nöd-fallback om locales.json är helt korrupt eller saknas
        self._hardcoded_fallback = {
            "en": {
                "voice_modes": ["OFF", "PTT", "LISTEN"],
                "app_title": "Voice Assistant",
                "status_ready": "Ready"
            },
            "sv": {
                "voice_modes": ["AV", "PTT", "LYSSNA"],
                "app_title": "Röstassistent",
                "status_ready": "Redo"
            }
        }
        
        # Läs in den externa JSON-datafilen omedelbart vid boot
        self.load_locales_from_disk()
        self.initialize_localization()

    def load_locales_from_disk(self) -> None:
        """Loads unstructured translation dictionaries transactionally into the memory map."""
        with self._lock:
            if os.path.exists(self.locales_path):
                try:
                    with open(self.locales_path, "r", encoding="utf-8") as f:
                        self._matrices = json.load(f)
                    print(f"[LOCALIZATION] Successfully serialized {len(self._matrices)} language matrices from disk.")
                except Exception as e:
                    print(f"[LOCALIZATION-ERROR] Failed to parse locales.json: {e}. Armed hardcoded fallbacks.")
                    # Sätt nöd-fallbacken om JSON-filen är korrupt
                    self._matrices = self._hardcoded_fallback.copy()
            else:
                print(f"[LOCALIZATION-WARNING] External data layer missing at {self.locales_path}. Fallbacks armed.")
                # Sätt nöd-fallbacken om filen saknas helt
                self._matrices = self._hardcoded_fallback.copy()

    def initialize_localization(self) -> None:
        """Determines the active host language vector transactionally at boot."""
        with self._lock:
            has_forced_preference = False
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    forced_lang = config.get("forced_language", "")
                    if forced_lang in self._matrices:
                        self.system_lang = forced_lang
                        has_forced_preference = True
                except Exception:
                    pass

            if not has_forced_preference:
                detected_iso = ""
                if sys.platform == "win32":
                    try:
                        import ctypes
                        # Förbättrad felhantering för ctypes-anropet
                        LOCALE_SISO639LANGNAME = 0x00000059
                        buf = ctypes.create_unicode_buffer(9)
                        result = ctypes.windll.kernel32.GetLocaleInfoW(0x0400, LOCALE_SISO639LANGNAME, buf, 9)
                        if result > 0:
                            detected_iso = buf.value.lower().strip()
                    except Exception:
                        pass

                if not detected_iso:
                    try:
                        for env_var in ["LANG", "LC_ALL", "LC_CTYPE"]:
                            val = os.environ.get(env_var, "").lower()
                            if "_" in val:
                                detected_iso = val.split("_")[0]
                                break
                            elif val:
                                detected_iso = val
                                break
                    except Exception:
                        pass

                if not detected_iso:
                    try:
                        loc = locale.getdefaultlocale() or locale.getlocale()
                        if loc and loc[0]:
                            detected_iso = loc[0].lower().split("_")[0]
                    except Exception:
                        pass

                if detected_iso in self._matrices:
                    self.system_lang = detected_iso
                else:
                    self.system_lang = "en"
            
            print(f"[LOCALIZATION] System language transaction bound to context: [{self.system_lang.upper()}]")

    def get_text(self, key: str) -> str:
        with self._lock:
            # Hämta från aktivt språk, fall tillbaka på engelska, fall tillbaka på hårdkodad engelska om allt raderats
            matrix = self._matrices.get(
                self.system_lang, 
                self._matrices.get("en", self._hardcoded_fallback.get("en", {}))
            )
            return matrix.get(key, f"[{key.upper()}_MISSING]")

    def get_voice_modes(self) -> list:
        with self._lock:
            matrix = self._matrices.get(
                self.system_lang, 
                self._matrices.get("en", self._hardcoded_fallback.get("en", {}))
            )
            return list(matrix.get("voice_modes", ["OFF", "PTT", "LISTEN"]))

```

==================================================
FILE: core/model_monitor_core.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: ai/ollama_client.py
 - CALLED BY: main/main.py, interface/client_gui.py
"""

import threading
import time
import ollama

class ModelMonitorCore:
    def __init__(self):
        self._lock = threading.Lock()

    def fetch_installed_models(self) -> list:
        """Queries local runtime environments to catalog current model inventory states."""
        try:
            model_list_data = ollama.list()
            return [m['model'] for m in model_list_data.get('models', [])]
        except Exception:
            return ["sailwind-pilot"]

    def start_lamp_monitor(self, core_hub_callback, update_lamp_ui_callback, get_switch_state_callback) -> None:
        """Spawns a specialized thread loop monitoring Ollama model availability matrix indexes."""
        def worker():
            while True:
                try:
                    if get_switch_state_callback() == 0:
                        update_lamp_ui_callback("#9CA3AF") # Standard Gray (OFF State)
                        time.sleep(1)
                        continue
                        
                    core = core_hub_callback()
                    if core and hasattr(core, 'ai_client'):
                        status = core.ai_client.check_model_status()
                        if status == "READY":
                            update_lamp_ui_callback("#10B981") # Green
                        elif status == "LOADING":
                            update_lamp_ui_callback("#F59E0B") # Yellow
                        else:
                            update_lamp_ui_callback("#EF4444") # Red
                except Exception:
                    break # Safe thread exit if interface structures tear down at closure
                time.sleep(3)

        threading.Thread(target=worker, daemon=True).start()


```

==================================================
FILE: core/path_core.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
GameBridge Path Core

KOPPLINGAR:
 - ANROPAS AV:
     - GameBridge-ramverket och övriga core-funktioner
 - ANVÄNDS AV:
     - ai.internet_transport.InternetTransport

ANSVAR:
 - Centraliserad och absolut sökvägshantering.
 - Ingen affärslogik.
 - Ingen AI-logik.
 - Ingen providerlogik.
 - Inga hårdkodade projektsökvägar.
"""

import os


class PathCore:
    # core/path_core.py ligger en nivå under projektroten.
    _CORE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(_CORE_DIR)

    @classmethod
    def get_absolute_path(cls, *paths: str) -> str:
        """Kombinerar sökvägar till en garanterad absolut sökväg."""
        return os.path.abspath(
            os.path.join(cls.PROJECT_ROOT, *paths)
        )

    @classmethod
    def get_config_path(
        cls,
        filename: str = "settings.json"
    ) -> str:
        """Returnerar absolut sökväg till global konfiguration."""
        return cls.get_absolute_path(
            "config",
            filename
        )

    @classmethod
    def get_adapter_root(cls) -> str:
        """Returnerar absolut sökväg till plugin-sfären."""
        return cls.get_absolute_path(
            "plugins"
        )

    @classmethod
    def get_adapter_file(
        cls,
        adapter_folder: str,
        filename: str
    ) -> str:
        """Returnerar absolut sökväg till en plugin-konfigurationsfil."""
        return cls.get_absolute_path(
            "plugins",
            adapter_folder,
            filename
        )

    @classmethod
    def get_internet_log_path(cls) -> str:
        """
        Returnerar absolut sökväg till GameBridges
        append-only-logg för internetförfrågningar.
        """
        return cls.get_absolute_path(
            "logs",
            "internet_queries.jsonl"
        )

```

==================================================
FILE: core/session_manager.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
CONNECTIONS:
  - FETCHES FROM: Isolated data layer (No external system dependencies).
  - CALLED BY: src/main.py, core/channel_matrix.py (State distribution vector)
"""

import threading
import copy
from typing import Dict, Any

class SessionManager:
    def __init__(self):
        # Thread-safe lock for asynchronous multi-threaded memory access
        self._lock = threading.Lock()
        
        # Standardized runtime state format matching framework specification
        self._state: Dict[str, Any] = {
            "session_active": False,
            "timestamp": 0.0,
            "current_adapter": "None",
            "active_hotkey": "None",          # ADDED: Tracks the active adapter's mapped hotkey dynamically
            "ai_infrastructure_active": False,
            "telemetry": {},
            "interaction_history": []
        }

    def update_state(self, key: str, value: Any) -> None:
        """Updates a specific value within the system runtime state in a thread-safe manner."""
        with self._lock:
            # FIX: Allow dynamic registration of adapter parameters without schema violation crashes
            if key in self._state or key.startswith("adapter_"):
                self._state[key] = value
                print(f"[STATE-UPDATED] Key '{key}' committed safely to runtime context.")
            else:
                # Fallback to absolute structural injection if initialized dynamically by adapter attachment
                self._state[key] = value
                print(f"[STATE-REGISTRATION] Dynamic runtime key '{key}' allocated safely: {value}")

    def set_telemetry(self, telemetry_data: Dict[str, Any]) -> None:
        """Deep-copies and flushes raw telemetry dictionaries into standardized storage."""
        with self._lock:
            self._state["telemetry"] = copy.deepcopy(telemetry_data)

    def get_standardized_state(self) -> Dict[str, Any]:
        """Returns a thread-isolated deep copy of the active state vector for safe reading."""
        with self._lock:
            return copy.deepcopy(self._state)

    def clear_session(self) -> None:
        """Flushes the active session data safely without executing destructive filesystem tasks."""
        with self._lock:
            self._state["telemetry"] = {}
            self._state["interaction_history"] = []
            self._state["current_adapter"] = "None"
            self._state["active_hotkey"] = "None"
            self._state["session_active"] = False
            print("[STATE] Active session parameters safely purged from runtime memory.")


```

==================================================
FILE: core/telemetry_core.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: core/io_layer.py, core/session_manager.py
 - CALLED BY: main/main.py, interface/client_gui.py
"""

import threading
import time

class TelemetryCore:
    def __init__(self, io_layer=None):
        self.io_layer = io_layer
        self.loop_active = False
        self._lock = threading.Lock()

    def set_loop_state(self, active: bool) -> None:
        """Safely mutates the background loop execution state vector across worker threads."""
        with self._lock:
            self.loop_active = active
            print(f"[TELEMETRY-CORE] Polling background thread status altered to: {active}")

    def start_polling_worker(self, current_adapter_callback, success_ui_callback) -> None:
        """Spawns an isolated thread sequence monitoring active context mutations asynchronously."""
        def worker():
            while True:
                with self._lock:
                    if not self.loop_active:
                        time.sleep(0.5)
                        continue
                
                active_instance = current_adapter_callback()
                if active_instance and self.io_layer:
                    try:
                        # Transactionally extract backend data streams via core IO layer boundaries
                        telemetry_data = self.io_layer.read_from_kanal_2()
                        if telemetry_data:
                            # Safely pass data back to presentation layer using the UI Queue
                            success_ui_callback(telemetry_data)
                    except Exception as e:
                        print(f"[TELEMETRY-CORE-ERROR] Synchronous backend telemetry extract faulted: {e}")
                
                time.sleep(1.0) # Standard stable polling interval

        threading.Thread(target=worker, daemon=True).start()

```

==================================================
FILE: functions/bridge_functions.py
TYPE: Kod
==================================================

```python
# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
 - HÄMTAR FRÅN: interface/audio_io.py, adapters/adapter_loader.py,
   ai/ollama_client.py, core/channel_matrix.py, interface/hardware_io.py,
   core/path_core.py, core/config_core.py, core/hotkey_capture_core.py,
   core/cognitive_router_core.py
 - ANROPAS AV: main/main.py, interface/client_gui.py
"""
import threading
import time
import os
import json
import sys
import keyboard
from interface.audio_io import AudioIO
from adapters.adapter_loader import AdapterLoader
from ai.ollama_client import OllamaClient
from interface.hardware_io import HardwareIO
from core.path_core import PathCore
from core.config_core import ConfigCore
from core.hotkey_capture_core import HotkeyCaptureCore
from core.cognitive_router_core import CognitiveRouterCore


# =========================================================================
# 1. PROCEDURFUNKTIONER (UTBRUTNA ENLIGT FAS C)
# =========================================================================

def function_play_welcome_message(audio_instance, gui_instance, current_voice_hotkey):
    """Asynchronously dispatches the audio confirmation chime and log events."""
    time.sleep(0.5)

    if sys.platform == "win32":
        import ctypes
        try:
            ctypes.windll.ole32.CoInitialize(None)
        except Exception:
            pass

    audio_instance.speak("System online.")

    if gui_instance:
        gui_instance.append_log(
            "SYSTEM",
            f"G.A.M.E. B.R.I.D.G.E. operational. "
            f"Baseline voice hotkey resolved to [{current_voice_hotkey.upper()}]."
        )

    if sys.platform == "win32":
        try:
            ctypes.windll.ole32.CoUninitialize()
        except Exception:
            pass


def function_setup_hardware_hotkeys(core_instance):
    """Thread worker loop supervising keyboard input and triggering voice modes."""
    error_count = 0

    while core_instance.running:
        if core_instance.gui and hasattr(core_instance.gui, "voice_mode_btn"):
            current_mode = core_instance.gui.voice_mode_btn.get()

            # GUI-presentation -> internal voice-mode contract.
            # The GUI uses icons; the voice/core layer uses stable semantic values.
            voice_mode_map = {
                "  🔇 ": "OFF",
                "🔘🎙️": "PTT",
                "  🎙️ ": "LISTEN",
                "OFF": "OFF",
                "AV": "OFF",
                "off": "OFF",
                "av": "OFF",
                "PTT": "PTT",
                "LISTEN": "LISTEN",
                "LYSSNA": "LISTEN",
            }

            normalized_mode = voice_mode_map.get(current_mode, current_mode)
            normalized_mode = str(normalized_mode).upper()

            if normalized_mode != "OFF":
                raw_target_key = core_instance.current_voice_hotkey

                try:
                    # Normalize the configured hotkey through HardwareIO.
                    normalized_key = core_instance.hardware.normalize_key(raw_target_key)

                    is_listen_mode = normalized_mode == "LISTEN"

                    # LISTEN starts automatically.
                    # PTT starts only while the configured hotkey is held.
                    if (
                        (is_listen_mode or keyboard.is_pressed(normalized_key))
                        and core_instance.voice
                        and not core_instance.voice.is_recording
                    ):
                        core_instance.voice.execute_ptt_transaction(
                            target_key=normalized_key,
                            running_check_callback=lambda: core_instance.running,
                            success_callback=core_instance.on_voice_token_resolved,
                            current_mode_callback=lambda: voice_mode_map.get(
                                core_instance.gui.voice_mode_btn.get(),
                                core_instance.gui.voice_mode_btn.get()
                            )
                        )

                    error_count = 0

                except Exception as e:
                    error_count += 1

                    if error_count <= 5:
                        print(f"[CORE-ERROR] Keyboard state scan faulted: {e}")
                    elif error_count == 6:
                        print(
                            "[CORE-WARNING] Keyboard errors repeating rapidly. "
                            "Silencing terminal output to protect performance."
                        )

        time.sleep(0.05)


# =========================================================================
# 2. HUVUDKLASS (TILLSTÅNDSDIRIGENT)
# =========================================================================

class GameBridgeCore:
    def __init__(self):
        self.gui = None
        self.audio = AudioIO()
        self.hardware = HardwareIO()
        self.matrix = None
        self.voice = None
        self.io_layer = None
        self.localizer = None
        self.telemetry_worker = None

        self.config_manager = ConfigCore()
        self.hotkey_capturer = HotkeyCaptureCore(self.hardware)
        self.cognitive_router = None

        self.active_adapter_instance = None
        self.current_adapter_folder = "None"

        self.is_listening = False
        self.running = True

        # EXPANSION v3.0: Användarkontrollerad capability för Internet AI
        self.internet_ai_enabled = False

        self.global_config = self.config_manager.load_global_config()
        self.config_path = self.config_manager.config_path

        self.current_voice_hotkey = self.global_config.get(
            "voice_hotkey",
            "f12"
        ).lower()

        self.ai_client = OllamaClient(
            model_name=self.global_config.get(
                "ai_model_name",
                "sailwind-pilot"
            )
        )

        try:
            self.loader = AdapterLoader(
                plugin_dir=PathCore.get_adapter_root()
            )
            self.available_adapters = self.loader.discover_and_load()
        except Exception as e:
            print(
                f"[CORE-ERROR] Dynamic extension discovery failed: {e}"
            )
            self.available_adapters = {}

    def link_gui(self, gui_instance):
        """Cross-references the presentation layer boundaries transactionally."""
        self.gui = gui_instance

        self.cognitive_router = CognitiveRouterCore(
            ai_client=self.ai_client,
            matrix=self.matrix,
            io_layer=self.io_layer,
            core_parent=self
        )

        is_eng = (
            hasattr(self.gui, "system_lang")
            and self.gui.system_lang == "en"
        )

        fallback_text = (
            "No Adapter Loaded"
            if is_eng
            else "Ingen Adapter Laddad"
        )

        adapter_list = [fallback_text]

        if self.available_adapters:
            adapter_list.extend(
                list(self.available_adapters.keys())
            )

        if self.gui and hasattr(self.gui, "adapter_selector"):
            self.gui.adapter_selector.configure(
                values=adapter_list
            )
            self.gui.adapter_selector.set(fallback_text)

        if self.gui and hasattr(self.gui, "internet_toggle"):
            initial_state = (
                "ON"
                if self.internet_ai_enabled
                else "OFF"
            )
            self.gui.internet_toggle.set(initial_state)

        if self.telemetry_worker:
            self.telemetry_worker.start_polling_worker(
                current_adapter_callback=lambda:
                    self.active_adapter_instance,
                success_ui_callback=lambda data:
                    self.gui.append_log(
                        "TELEMETRY",
                        str(data)
                    )
                    if self.gui
                    else print(data)
            )

    def update_internet_capability(self, enabled: bool):
        """Transactional setter invoked by UI event queue to flip internet capability state."""
        self.internet_ai_enabled = enabled

        log_msg = (
            "Internet AI capability activated (Port 8080 route armed)."
            if enabled
            else
            "Internet AI capability deactivated "
            "(Offline/Local enforcement active)."
        )

        if self.gui:
            self.gui.append_log("SYSTEM", log_msg)

    def boot_platform_loops(self):
        """Unified entry point invoking isolated background executions."""
        threading.Thread(
            target=function_setup_hardware_hotkeys,
            args=(self,),
            daemon=True
        ).start()

        threading.Thread(
            target=function_play_welcome_message,
            args=(
                self.audio,
                self.gui,
                self.current_voice_hotkey
            ),
            daemon=True
        ).start()

    def load_adapter_specific_hotkey(self):
        """Reflectively extracts runtime subdirectory names and dynamically binds hotkeys."""
        if not self.active_adapter_instance:
            self.current_adapter_folder = "None"
            self.global_config = (
                self.config_manager.load_global_config()
            )

            self.current_voice_hotkey = self.global_config.get(
                "voice_hotkey",
                "f12"
            ).lower()

            return

        module_name = (
            self.active_adapter_instance.__class__.__module__
        )

        parts = module_name.split(".")

        if len(parts) >= 1:
            self.current_adapter_folder = parts[0]
        else:
            self.current_adapter_folder = "None"

        config_file = PathCore.get_adapter_file(
            self.current_adapter_folder,
            "plugin_config.json"
        )

        if os.path.exists(config_file):
            try:
                with open(
                    config_file,
                    "r",
                    encoding="utf-8"
                ) as f:
                    plugin_data = json.load(f)

                self.current_voice_hotkey = plugin_data.get(
                    "voice_hotkey",
                    self.global_config.get(
                        "voice_hotkey",
                        "f12"
                    )
                ).lower()

                print(
                    f"[CORE] Dynamic hotkey hot-swap execution: "
                    f"[{self.current_voice_hotkey.upper()}] "
                    f"bended to {self.current_adapter_folder}"
                )

                return

            except Exception:
                pass

        self.current_voice_hotkey = self.global_config.get(
            "voice_hotkey",
            "f12"
        ).lower()

    def handle_adapter_switch(self, adapter_name: str):
        """Safely hot-swaps active adapter interfaces on the execution stack."""
        if adapter_name in self.available_adapters:
            if self.active_adapter_instance:
                self.active_adapter_instance.shutdown()

            adapter_class = self.available_adapters[adapter_name]
            self.active_adapter_instance = adapter_class()
            self.active_adapter_instance.initialize()

            if self.io_layer:
                self.io_layer.register_adapter_channels(
                    input_cb=self.active_adapter_instance.execute_interaction,
                    output_cb=self.active_adapter_instance.read_telemetry
                )

            self.load_adapter_specific_hotkey()

            if self.gui:
                self.gui.append_log(
                    "SYSTEM",
                    f"Extension stack mutated. "
                    f"Allocated runtime focus to '{adapter_name}'."
                )

    def unload_active_adapter(self):
        """Detaches active extension frameworks, reverting state boundaries."""
        if self.active_adapter_instance:
            self.active_adapter_instance.shutdown()

        self.active_adapter_instance = None
        self.current_adapter_folder = "None"

        self.global_config = (
            self.config_manager.load_global_config()
        )

        self.current_voice_hotkey = self.global_config.get(
            "voice_hotkey",
            "f12"
        ).lower()

    def boot_target_application(self):
        """Asynchronously executes target app boot processes via adapter hooks."""
        if self.active_adapter_instance:
            threading.Thread(
                target=self.active_adapter_instance.boot_or_attach,
                daemon=True
            ).start()
        else:
            if self.gui:
                self.gui.append_log(
                    "SYSTEM-WARNING",
                    "Execution request denied: "
                    "No target extension currently deployed."
                )

    def set_channels_state(self, k1: bool, k2: bool):
        """Enforces routing authorization flags for internal cross-transference."""
        if self.matrix:
            self.matrix.update_states(
                k1,
                k2,
                self.matrix.ai_generation_enabled,
                self.matrix.internet_ai_enabled
            )

    def capture_new_hotkey(self):
        """Leverages the decoupled HotkeyCaptureCore to intercept raw peripheral events safely."""
        if not self.gui or not self.hotkey_capturer:
            return

        def _before():
            pass

        def _success(cleaned_key: str):
            self.current_voice_hotkey = cleaned_key

            if (
                self.active_adapter_instance
                and self.current_adapter_folder != "None"
            ):
                self.config_manager.save_adapter_hotkey(
                    self.current_adapter_folder,
                    cleaned_key
                )

                self.gui.append_log(
                    "SYSTEM",
                    f"Dynamic hotkey persisted to target "
                    f"extension workspace: [{cleaned_key.upper()}]"
                )
            else:
                self.global_config["voice_hotkey"] = cleaned_key

                self.config_manager.save_global_config(
                    self.global_config
                )

                self.gui.append_log(
                    "SYSTEM",
                    f"Dynamic hotkey persisted to global engine "
                    f"configuration: [{cleaned_key.upper()}]"
                )

        def _final():
            is_eng = (
                getattr(self.gui, "system_lang", "en")
                == "en"
            )

            self.gui.status_label.configure(
                text="Status: Ready"
                if is_eng
                else "Status: Redo"
            )

            if hasattr(self.gui, "hotkey_btn"):
                self.gui.hotkey_btn.configure(
                    fg_color="#374151"
                )

        self.hotkey_capturer.capture_next_keypress(
            _before,
            _success,
            _final
        )

    def on_voice_token_resolved(self, recognized_text: str):
        """Callback executed transactionally by VoiceCore when clean text tokens are decoded."""
        if self.gui:
            sender_tag = (
                "USER (Channel 1)"
                if getattr(self.gui, "system_lang", "en") == "en"
                else "ANVÄNDARE (Kanal 1)"
            )

            self.gui.append_log(
                sender_tag,
                recognized_text
            )

        self.process_chatt_flow(recognized_text)

    def process_chatt_flow(self, user_text: str):
        """Relays cognitive token tracking safely through the decoupled router core sub-system."""
        if not self.cognitive_router:
            return

        def _ui_status(state: str):
            if self.gui:
                is_eng = (
                    getattr(self.gui, "system_lang", "en")
                    == "en"
                )

                if state == "PROCESSING":
                    self.gui.status_label.configure(
                        text=(
                            "Status: Processing..."
                            if is_eng
                            else "Status: Processar..."
                        )
                    )
                else:
                    self.gui.status_label.configure(
                        text=(
                            "Status: Ready"
                            if is_eng
                            else "Status: Redo"
                        )
                    )

        def _gui_log(sender: str, text: str):
            if self.gui:
                self.gui.append_log(sender, text)

        def _speech(text_to_speak: str):
            if self.gui and hasattr(
                self.gui,
                "voice_mode_btn"
            ):
                current_mode = self.gui.voice_mode_btn.get()

                voice_mode_map = {
                    "  🔇 ": "OFF",
                    "🔘🎙️": "PTT",
                    "  🎙️ ": "LISTEN",
                    "OFF": "OFF",
                    "AV": "OFF",
                    "off": "OFF",
                    "av": "OFF",
                    "PTT": "PTT",
                    "LISTEN": "LISTEN",
                    "LYSSNA": "LISTEN",
                }

                normalized_mode = voice_mode_map.get(
                    current_mode,
                    current_mode
                )

                if str(normalized_mode).upper() != "OFF":
                    if hasattr(self, "audio") and self.audio:
                        threading.Thread(
                            target=self.audio.speak,
                            args=(text_to_speak,),
                            daemon=True
                        ).start()

        self.cognitive_router.route_transactional_flow(
            user_text=user_text,
            active_adapter=self.active_adapter_instance,
            adapter_folder=self.current_adapter_folder,
            gui_log_callback=_gui_log,
            ui_status_callback=_ui_status,
            speech_callback=_speech
        )

```

==================================================
FILE: functions/internet_functions.py
TYPE: Kod
==================================================

```python
# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
 - HÄMTAR FRÅN: Pythons standardbibliotek (webbrowser)
 - ANROPAS AV: functions/router_functions.py
"""
import webbrowser
import threading

def function_open_browser_link(url_str: str):
    """Asynchronously dispatches a clean URL string to the host OS standard browser execution layer."""
    if not url_str:
        return
        
    def browser_worker():
        try:
            # Rensa eventuellt brus från strängen och öppna i standardwebbläsaren
            clean_url = url_str.strip().strip('"').strip("'")
            # Enforce strict web protocol prefixes if missing
            if not clean_url.startswith(("http://", "https://")):
                clean_url = "https://" + clean_url
                
            print(f"[INTERNET-BRIDGE] Launching default OS browser layer for payload: {clean_url}")
            webbrowser.open(clean_url, new=2) # new=2 opens in a new tab if browser is alive
        except Exception as e:
            print(f"[INTERNET-BRIDGE-ERROR] Failed to dispatch browser thread: {e}")

    threading.Thread(target=browser_worker, daemon=True).start()

```

==================================================
FILE: functions/router_functions.py
TYPE: Kod
==================================================

```python
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
            # REN FIX: Prioritera adapterns egna read_telemetry() för kanal-2 data.
            # Inga hårda strängar eller filter – vi bara styr om datakällan rätt.
            if hasattr(active_adapter, "read_telemetry"):
                telemetry = active_adapter.read_telemetry()
            elif router_instance.io_layer:
                telemetry = router_instance.io_layer.read_from_kanal_2()
            
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

        # ORIGINAL-FLÖDE ÅTERSTÄLLT: Inga hårda villkor eller dämpningar i routern.
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

```

==================================================
FILE: functions/__init__.py
TYPE: Kod
==================================================

```python


```

==================================================
FILE: interface/audio_io.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
CONNECTIONS:
  - FETCHES FROM: No internal logic files (External hardware binding layer).
  - CALLED BY: core/bridge_core.py
"""

import pyttsx3
import speech_recognition as sr

class AudioIO:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Adjusted pause threshold to resolve human vocal patterns faster
        self.recognizer.pause_threshold = 1.0 

    def speak(self, text: str):
        """Asynchronously initializes the local TTS engine to output vocal tokens."""
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 160)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[AUDIO-ERROR] Text-to-speech engine execution failed: {e}")

    def listen(self) -> str:
        """Opens the hardware audio vector, capturing speech data safely without rigid blocking timeouts."""
        try:
            with sr.Microphone() as source:
                print("[SYSTEM] Audio intercept active (Channel 1 stream). Awaiting speech...")
                # Dynamically sample ambient background noise before capturing tokens
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                
                # Dynamic capture: Removed the hard timeout barrier that caused thread blocking crashes
                audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=8.0)
                
            # Enforces native Swedish token interpretation for core interaction flows
            return self.recognizer.recognize_google(audio, language="sv-SE")
        except Exception as e:
            print(f"[AUDIO-DEBUG] Audio capture transaction details: {e}")
            return ""


```

==================================================
FILE: interface/background.png
TYPE: Bild
==================================================

[BINARY - innehåll ej inkluderat]

==================================================
FILE: interface/chat_window.py
TYPE: Kod
==================================================

```python
# -*- coding: utf-8 -*-
"""
GameBridge 16:9 HTML Chat Presentation Component
KOPPLINGAR:
 - HÄMTAR FRÅN:
   - core/path_core.py (för absolut sökväg till bakgrundsbild)
 - ANROPAS AV:
   - interface/client_gui.py
 - EXTERNA ANROP:
   - interface/gui_functions.py (via inskickade callbacks från client_gui)
"""
import customtkinter as ctk
from tkinterweb import HtmlFrame
import os
import re
from core.path_core import PathCore

class ChatWindow(ctk.CTkFrame):
    def __init__(self, master, localizer=None, handle_log_click_callback=None, **kwargs):
        """
        En presentationsvy i 16:9-format baserad på HTML/CSS som sköter 
        skalningen internt i webb-motorn för att undvika fönsterhopp.
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.localizer = localizer
        self.handle_log_click_callback = handle_log_click_callback
        
        self.bg_image_path = PathCore.get_absolute_path("interface", "background.png")
        
        # Interna tillstånd för textstil
        self.is_large_text = False
        self.is_black_text = False
        
        # Aktuell dynamisk zoomfaktor baserat på basmåttet 960 bredd
        self.current_scale_factor = 1.0
        
        # Datacache för att bygga om HTML-vyn dynamiskt
        self.messages_cache = []
        self.monitor_cache = []
        self.monitor_visible = False
        self._build_components()

    @property
    def log_box(self):
        """Property-länk för bakåtkompatibilitet med gui_functions."""
        return self

    def _build_components(self):
        """Skapar och förbereder HTML-presentationsytan."""
        # ANKARE 1 (Python): Webb-visaren fixeras i NW och fyller ut 16:9-ramen fullt ut
        self.html_viewer = HtmlFrame(self)
        self.html_viewer.place(relx=0.0, rely=0.0, anchor="nw", relwidth=1.0, relheight=1.0)
        
        if self.handle_log_click_callback:
            self.html_viewer.bind("<Button-1>", lambda event:
                self.handle_log_click_callback(self, event))
        
        # Bind egna storleksförändringar för att räkna ut den två-hörnsbaserade skalfaktorn
        self.bind("<Configure>", self._on_window_resized)
        self._refresh_presentation_layer()

    def _on_window_resized(self, event):
        """Räknar ut den exakta skalfaktorn i förhållande till basmåttet 960."""
        if event.width <= 1:
            return
        # Beräkna hur mycket större fönstret är än basmåttet 960
        new_scale = event.width / 960.0
        
        # Förhindra onödiga omladdningar om storleken knappt ändrats
        if abs(self.current_scale_factor - new_scale) > 0.01:
            self.current_scale_factor = new_scale
            self._refresh_presentation_layer()

    def _refresh_presentation_layer(self):
        """Genererar CSS och HTML där bilden spänns upp i 16:9 och texten scrollar."""
        img_element = ""
        if os.path.exists(self.bg_image_path):
            file_url = self.bg_image_path.replace("\\\\", "/").replace("\\", "/")
            # Skapar ett fysiskt bild-lager som tvingas skala stenhårt med dokumentets ramar
            img_element = f"<img class='bg-image-layer' src='file:///{file_url}' />"
        
        text_color = "#000000" if self.is_black_text else "#FFFFFF"
        font_size = "18px" if self.is_large_text else "14px"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        html, body {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            background-color: #1E293B;
            overflow: hidden;
            box-sizing: border-box;
        }}
        /* Bildlagret låses i NW och sträcks ut fysiskt till SW och SE i takt med fönsterskalningen */
        .bg-image-layer {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: fill; /* Tvingar bilden att följa de uppspända ankarmåtten slaviskt */
            z-index: 1;
        }}
        /* Chat-containern ligger ovanpå bilden och skalar linjärt från det fasta NW-ankaret */
        .chat-container {{
            position: absolute;
            top: 0;
            left: 0;
            width: 960px; /* Håller basupplösningen konstant internt */
            height: 540px;
            padding: 20px;
            box-sizing: border-box;
            overflow-y: auto;
            transform: scale({self.current_scale_factor});
            transform-origin: left top; /* Säkrar att all textuträkning utgår stenhårt från NW */
            z-index: 2;
        }}
        .msg-line {{
            padding: 6px 10px;
            margin-bottom: 5px;
            background: rgba(15, 23, 42, 0.6);
            border-radius: 6px;
            font-family: 'Consolas', monospace;
            color: {text_color};
            font-size: {font_size};
        }}
        .monitor-area {{
            margin-top: 15px;
            padding: 10px;
            background: rgba(9, 13, 22, 0.9);
            border: 1px solid #10B981;
            border-radius: 6px;
            color: #10B981;
            font-size: 12px;
            font-family: 'Consolas', monospace;
        }}
        </style>
        </head>
        <body>
        {img_element}
        <div class="chat-container">
        """
        
        for sender, text in self.messages_cache:
            html_content += f"<div class='msg-line'><strong>[{sender}]:</strong> {text}</div>"
        
        if self.monitor_visible and self.monitor_cache:
            html_content += "<div class='monitor-area'><strong>■ KANAL 2 MONITOR:</strong>"
            for log_line in self.monitor_cache:
                html_content += f"<br>{log_line}"
            html_content += "</div>"
        
        html_content += """
        </div>
        </body>
        </html>
        """
        self.html_viewer.load_html(html_content)

    def append_chat_message(self, sender: str, text: str):
        self.messages_cache.append((sender, text))
        self._refresh_presentation_layer()

    def append_monitor_message(self, text: str):
        self.monitor_cache.append(text)
        if self.monitor_visible:
            self._refresh_presentation_layer()

    def set_text_dimensions(self, make_large: bool):
        self.is_large_text = make_large
        self._refresh_presentation_layer()

    def set_text_mode_black(self, black_mode: bool):
        self.is_black_text = black_mode
        self._refresh_presentation_layer()

    def set_monitor_visibility(self, visible: bool):
        self.monitor_visible = visible
        self._refresh_presentation_layer()

```

==================================================
FILE: interface/client_gui.py
TYPE: Kod
==================================================

```python
# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
- HÄMTAR FRÅN: interface/ui_event_queue.py, core/telemetry_core.py, 
core/model_monitor_core.py, interface/gui_functions.py, interface/chat_window.py,
core/path_core.py
- ANROPAS AV: main/main.py
"""
import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import threading
import re
import os
import sys

from core.path_core import PathCore
from interface.ui_event_queue import UIEventQueue
from core.telemetry_core import TelemetryCore
from core.model_monitor_core import ModelMonitorCore
from interface.chat_window import ChatWindow
from interface.gui_functions import (
    function_on_ai_toggle, function_on_internet_toggle, function_sync_matrix_to_core,
    function_on_telemetry_toggle, function_on_lock_toggle, function_on_model_change, 
    function_on_adapter_change, function_trigger_text_input, function_handle_log_double_click
)

class GameBridgeGUI(ctk.CTk):
    def __init__(self, core_hub=None, matrix=None, localizer=None):
        super().__init__()
        
        # FIXED: Beroenden injiceras omedelbart i konstruktorn för att säkra språksynken vid boot
        self.core_hub = core_hub
        self.matrix = matrix 
        self.localizer = localizer 
        self.version = "3.5.0"
        
        self.event_queue = UIEventQueue()
        self.model_monitor = ModelMonitorCore()
        
        # Fönstret startar som överst, men kan muteras dynamiskt av användaren
        self.attributes("-topmost", True)
        
        # UTRENSAD: Ingen hårdkodad geometry eller 960x540-låsning på fönsternivå längre! 🔓
        
        self._build_ui()
        self._process_gui_queue_loop()
    def on_ai_toggle(self):
        function_on_ai_toggle(self)

    def on_internet_toggle(self):
        function_on_internet_toggle(self)

    def on_topmost_toggle(self):
        """Dynamically flips the OS window layering priority based on user check state."""
        if hasattr(self, 'topmost_toggle_switch'):
            is_on = self.topmost_toggle_switch.get() == 1
            self.attributes("-topmost", is_on)
            state_msg = "Always-on-Top activated." if is_on else "Always-on-Top deactivated. Background persistence active."
            self.append_log("SYSTEM", state_msg)

    def sync_matrix_to_core(self):
        function_sync_matrix_to_core(self)

    def on_telemetry_toggle(self):
        function_on_telemetry_toggle(self)

    def on_lock_toggle(self):
        # FIXED: Slussas nu transaktionellt ut till gui_functions för att mutera HardwareIO
        function_on_lock_toggle(self)
        if hasattr(self, 'lock_icon_label') and hasattr(self, 'lock_switch'):
            icon = "⌨️🔒" if self.lock_switch.get() == 1 else "⌨️🔓"
            self.lock_icon_label.configure(text=icon)

    def on_voice_mode_change(self, mode):
        pass

    def _safe_update_lamp_color(self, color_hex: str):
        self.event_queue.dispatch(lambda: self.ai_status_lamp.configure(text_color=color_hex))

    def start_hotkey_capture(self):
        if self.core_hub:
            self.hotkey_btn.configure(text="  ⌨️⏳", fg_color="#DC2626")
            threading.Thread(target=self.core_hub.capture_new_hotkey, daemon=True).start()

    def on_model_change(self, selected_model):
        function_on_model_change(self, selected_model)
        
    # BACKÅTKOMPATIBILITET FÖR GUI_FUNCTIONS
    @property
    def log_box(self):
        return self.chat_window.log_box
        
    @property
    def entry_field(self):
        return self.entry_field_widget

    def append_log(self, sender: str, text: str):
        """Slussar vidare meddelandet trådsäkert till det nya externa chatfönstret."""
        self.chat_window.append_chat_message(sender, text)

    def _process_gui_queue_loop(self):
        self.event_queue.process_next_batch()
        self.after(50, self._process_gui_queue_loop)
    def on_adapter_change(self, selected_adapter):
        """Växlar adapter och uppdaterar den kombinerade Connect/Disconnect-knappens utseende."""
        function_on_adapter_change(self, selected_adapter)
        
        no_adapter_text = self.localizer.get_text("no_adapter") if self.localizer else "No Adapter Loaded"
        
        if selected_adapter == no_adapter_text:
            boot_str = self.localizer.get_text("boot_btn") if self.localizer else "Launch / Attach App"
            self.boot_target_btn.configure(text=boot_str, fg_color="#059669", hover_color="#10B981", state="disabled")
        else:
            boot_str = self.localizer.get_text("boot_btn") if self.localizer else "Launch / Attach App"
            self.boot_target_btn.configure(text=boot_str, fg_color="#059669", hover_color="#10B981", state="normal")

    def trigger_combined_adapter_action(self):
        """Hanterar både Connect och Disconnect i en och samma knapp baserat på dess nuvarande tillstånd."""
        no_adapter_text = self.localizer.get_text("no_adapter") if self.localizer else "No Adapter Loaded"
        disconnect_str = self.localizer.get_text("disconnect_btn") if self.localizer else "Disconnect"
        
        if self.boot_target_btn.cget("text") == disconnect_str:
            self.adapter_selector.set(no_adapter_text)
            self.on_adapter_change(no_adapter_text)
        else:
            if self.core_hub:
                self.append_log("SYSTEM", "Initializing manual boot sequence...")
                self.core_hub.boot_target_application()
            
            self.boot_target_btn.configure(text=disconnect_str, fg_color="#DC2626", hover_color="#EF4444")

    def trigger_text_input(self):
        function_trigger_text_input(self)

    # REGLAGEMETODER SOM PRATAR MED DET EXTERNA CHATTFÖNSTRET
    def on_text_size_toggle(self):
        is_large = self.text_size_switch.get() == 1
        self.chat_window.set_text_dimensions(is_large)

    def on_text_color_toggle(self):
        is_black = self.text_color_switch.get() == 1
        self.chat_window.set_text_mode_black(is_black)

    def toggle_monitor_panel(self):
        is_visible = self.monitor_switch.get() == 1
        self.chat_window.set_monitor_visibility(is_visible)
    def _build_ui(self):
        """Renders standard application layout widgets using current localization strings with strict fallbacks."""
        title_str = self.localizer.get_text("title") if self.localizer else "G.A.M.E. B.R.I.D.G.E."
        self.title(title_str)
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        
        # 1. TOP PANEL FRAME AND CORE WIDGETS
        self.top_frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        self.top_frame.pack(pady=(10, 5), padx=10, fill="x")
        self.ai_status_lamp = ctk.CTkLabel(self.top_frame, text="●", text_color="#9CA3AF", font=("Arial", 22))
        self.ai_status_lamp.pack(side="left", padx=(15, 5), pady=10)
        status_str = self.localizer.get_text("status_ready") if self.localizer else "Status: Ready"
        self.status_label = ctk.CTkLabel(self.top_frame, text=status_str, font=("Arial", 13, "bold"))
        self.status_label.pack(side="left", padx=5, pady=10)
        
        ai_toggle_str = self.localizer.get_text("ai_toggle") if self.localizer else "AI Active"
        self.ai_toggle_switch = ctk.CTkSwitch(self.top_frame, text=ai_toggle_str, command=self.on_ai_toggle, font=("Arial", 12, "bold"))
        self.ai_toggle_switch.pack(side="left", padx=10, pady=10)
        self.ai_toggle_switch.deselect()
        
        internet_toggle_str = self.localizer.get_text("internet_toggle") if self.localizer else "Internet AI"
        self.internet_toggle = ctk.CTkSwitch(self.top_frame, text=internet_toggle_str, command=self.on_internet_toggle, font=("Arial", 12, "bold"), progress_color="#10B981")
        self.internet_toggle.pack(side="left", padx=10, pady=10)
        self.internet_toggle.deselect()
        
        boot_str = self.localizer.get_text("boot_btn") if self.localizer else "Launch / Attach App"
        self.boot_target_btn = ctk.CTkButton(self.top_frame, text=boot_str, command=self.trigger_combined_adapter_action, width=150, fg_color="#059669", hover_color="#10B981", state="disabled")
        self.boot_target_btn.pack(side="right", padx=(15, 15), pady=10)
        
        no_adapter_text = self.localizer.get_text("no_adapter") if self.localizer else "No Adapter Loaded"
        initial_adapters = [no_adapter_text]
        if self.core_hub and hasattr(self.core_hub, 'available_adapters'):
            discovered = list(self.core_hub.available_adapters.keys())
            if discovered:
                initial_adapters.extend(discovered)
        self.adapter_selector = ctk.CTkOptionMenu(self.top_frame, values=initial_adapters, command=self.on_adapter_change)
        self.adapter_selector.pack(side="right", padx=10, pady=10)
        self.adapter_selector.set(no_adapter_text)
        self.model_selector = ctk.CTkOptionMenu(self.top_frame, values=self.model_monitor.fetch_installed_models(), command=self.on_model_change)
        self.model_selector.pack(side="right", padx=10, pady=10)
        if self.core_hub and hasattr(self.core_hub, 'global_config'):
            saved_model = self.core_hub.global_config.get("ai_model_name", "sailwind-pilot")
            if saved_model in self.model_selector.cget("values"):
                self.model_selector.set(saved_model)
        
        # 2. SIGNAL INSTRUMENT MATRIX FRAME
        self.matrix_frame = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color="#1E293B")
        self.matrix_frame.pack(pady=5, padx=10, fill="x")
        matrix_title_str = self.localizer.get_text("matrix_title") if self.localizer else "CHANNEL CONTROL"
        self.matrix_title = ctk.CTkLabel(self.matrix_frame, text=matrix_title_str, font=("Arial", 11, "bold"), text_color="#94A3B8")
        self.matrix_title.pack(anchor="w", padx=15, pady=(8, 2))
        self.controls_grid = ctk.CTkFrame(self.matrix_frame, fg_color="transparent")
        self.controls_grid.pack(fill="x", padx=15, pady=(0, 10))
        
        # 3. POPULATE THE CONTROLS GRID
        chat_switch_str = (
            self.localizer.get_text("chat_switch")
            if self.localizer
            else "Text Chat"
        )
        self.chat_switch = ctk.CTkSwitch(
            self.controls_grid,
            text=chat_switch_str,
            command=self.sync_matrix_to_core,
            font=("Arial", 12),
            text_color="#E2E8F0",
        )
        self.chat_switch.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.chat_switch.deselect()
        
        voice_label_str = (
            self.localizer.get_text("voice_label")
            if self.localizer
            else "Voice Mode:"
        )
        self.voice_label = ctk.CTkLabel(
            self.controls_grid,
            text=voice_label_str,
            font=("Arial", 12),
            text_color="#E2E8F0",
        )
        self.voice_label.grid(
            row=0, column=1, padx=(20, 5), pady=10, sticky="w"
        )

        # Originalikoner där Av och Lyssna görs 2 pixlar större i relation till mittenikonen
        voice_modes_list = ["  🔇 ", "🔘🎙️", "  🎙️ "]
        voice_mode_values = ["OFF", "PTT", "LISTEN"]

        self.voice_mode_btn = ctk.CTkSegmentedButton(
            self.controls_grid,
            values=voice_modes_list,
            command=lambda mode: self.on_voice_mode_change(
                voice_mode_values[voice_modes_list.index(mode)]
            ),
            font=("Arial", 14),
            selected_color="#3B82F6",  # Standard blå dropdown-färg som bas
        )
        self.voice_mode_btn.grid(row=0, column=2, padx=5, pady=10, sticky="w")
        self.voice_mode_btn.set(voice_modes_list[0])
        
        # Dynamisk färg- och storlekskodning (Röd för Av, Grön för PTT/Listen)
        def _update_voice_btn_color(mode):
            if mode == "  🔇 ":
                self.voice_mode_btn.configure(selected_color="#DC2626", font=("Arial", 16)) # 2px större för 🔇
            elif mode == "🔘🎙️":
                self.voice_mode_btn.configure(selected_color="#059669", font=("Arial", 14)) # Standard för mitten
            elif mode == "  🎙️ ":
                self.voice_mode_btn.configure(selected_color="#059669", font=("Arial", 16)) # 2px större för 🎙️
        
        # Hooka färg/storleksändringen utan att röra GameBridge-logiken
        orig_voice_change = self.on_voice_mode_change
        def _wrapped_voice_change(mode):
            _update_voice_btn_color(mode)
            orig_voice_change(mode)
        self.voice_mode_btn.configure(command=_wrapped_voice_change)
        _update_voice_btn_color(voice_modes_list[0])
        
        tel_switch_str = self.localizer.get_text("telemetry_switch") if self.localizer else "Read Telemetry"
        self.read_telemetry_switch = ctk.CTkSwitch(self.controls_grid, text=tel_switch_str, command=self.on_telemetry_toggle, font=("Arial", 12), text_color="#E2E8F0")
        self.read_telemetry_switch.grid(row=0, column=3, padx=40, pady=10, sticky="w")
        self.read_telemetry_switch.deselect()
        write_switch_str = self.localizer.get_text("write_switch") if self.localizer else "Write to Adapter"
        self.write_adapter_switch = ctk.CTkSwitch(self.controls_grid, text=write_switch_str, command=self.sync_matrix_to_core, font=("Arial", 12), text_color="#E2E8F0")
        self.write_adapter_switch.grid(row=0, column=4, padx=20, pady=10, sticky="w")
        self.write_adapter_switch.deselect()

        # 5. LOWER FRAME INTERACTIVE INPUT CONTROLS
        self.control_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.control_frame.pack(pady=(0, 5), padx=10, fill="x", side="bottom")
        
        # Låsikon uppdaterad till originaletikett med 2px större tangentbordsikon till vänster
        self.lock_icon_label = ctk.CTkLabel(self.control_frame, text="⌨️🔓", font=("Arial", 16))
        self.lock_icon_label.pack(side="left", padx=(5, 2))
        
        self.lock_switch = ctk.CTkSwitch(self.control_frame, text="", command=self.on_lock_toggle, width=45)
        self.lock_switch.pack(side="left", padx=(0, 15))
        self.lock_switch.deselect()
        
        # Säkerställ att ikonen ändras till stängd vid toggle utan att bryta GameBridge-logiken högre upp
        orig_lock_toggle = self.on_lock_toggle
        def _wrapped_lock_toggle():
            orig_lock_toggle()
            # Överskriver texten direkt här nere för att matcha din nya ikondesign och storlek
            icon = "⌨️🔒" if self.lock_switch.get() == 1 else "⌨️🔓"
            self.lock_icon_label.configure(text=icon)
        self.lock_switch.configure(command=_wrapped_lock_toggle)
        
        topmost_str = self.localizer.get_text("topmost_toggle") if self.localizer else "Stay on Top"
        self.topmost_toggle_switch = ctk.CTkSwitch(self.control_frame, text=topmost_str, command=self.on_topmost_toggle, font=("Arial", 12), progress_color="#3B82F6")
        self.topmost_toggle_switch.pack(side="left", padx=10)
        self.topmost_toggle_switch.select()
        
        self.text_size_switch = ctk.CTkSwitch(self.control_frame, text="🔍 Stor text", command=self.on_text_size_toggle)
        self.text_size_switch.pack(side="left", padx=10)
        
        self.text_color_switch = ctk.CTkSwitch(self.control_frame, text="● Svart text", command=self.on_text_color_toggle)
        self.text_color_switch.pack(side="left", padx=10)
        self.text_color_switch.deselect()
        
        self.monitor_switch = ctk.CTkSwitch(self.control_frame, text="● K2 Mon", command=self.toggle_monitor_panel)
        self.monitor_switch.pack(side="left", padx=10)
        
        # Hotkey-knapp utan plus ( 🔘🎙️) och med 2px större storlek (font 16)
        self.hotkey_btn = ctk.CTkButton(
            self.control_frame, 
            text="  🔘🎙️", 
            command=self.start_hotkey_capture, 
            width=65, 
            font=("Arial", 16, "bold"), 
            fg_color="#374151", 
            hover_color="#4B5563"
        )
        self.hotkey_btn.pack(side="right", padx=5)
        # INTERAKTIV INMATNINGSRAD (Ligger fast i botten, under allt annat)
        self.bottom_input_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.bottom_input_frame.pack(pady=10, padx=10, fill="x", side="bottom")
        
        placeholder_str = self.localizer.get_text("input_placeholder") if self.localizer else "Type message..."
        self.entry_field_widget = ctk.CTkEntry(self.bottom_input_frame, placeholder_text=placeholder_str, font=("Arial", 12))
        self.entry_field_widget.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_field_widget.bind("<Return>", lambda event: self.trigger_text_input())
        
        send_str = self.localizer.get_text("send_btn") if self.localizer else "Send"
        self.send_button = ctk.CTkButton(self.bottom_input_frame, text=send_str, command=self.trigger_text_input, width=100)
        self.send_button.pack(side="right")
        
        # 4. MONTERING AV EXTERN CHATTKOMPONENT (CHATWINDOW PRESENTATION)
        # Justerar de övriga panelerna så att de förankras strikt mot fönstret
        self.top_frame.pack_configure(side="top", fill="x", expand=False)
        self.matrix_frame.pack_configure(side="top", fill="x", expand=False)
        self.bottom_input_frame.pack_configure(side="bottom", fill="x", expand=False)
        self.control_frame.pack_configure(side="bottom", fill="x", expand=False)

        # Skapar mittensektionen som tar upp allt resterande utrymme i fönstret
        self.chat_anchor_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.chat_anchor_container.pack(pady=5, padx=10, fill="both", expand=True)

        # Det fasta 16:9-ankaret (låst till NW) fungerar nu som den fasta yttre ramen
        self.chat_anchor_surface = ctk.CTkFrame(self.chat_anchor_container, fg_color="#10172A")
        self.chat_anchor_surface.place(relx=0.0, rely=0.0, anchor="nw")

        # Laddar in det riktiga presentationslagret (ChatWindow) direkt i vårt 16:9-ankare
        self.chat_window = ChatWindow(
            master=self.chat_anchor_surface,
            localizer=self.localizer,
            handle_log_click_callback=function_handle_log_double_click
        )
        # Låter presentationen, bakgrundsbilden och texterna fylla ut hela ankarytan
        self.chat_window.pack(fill="both", expand=True)

        def _enforce_16_9_aspect(event=None):
            # Tvinga fönsterhanteraren att beräkna de exakta måtten för övriga paneler
            self.update_idletasks()
            
            # Räkna ut exakt hur mycket plats de andra GUI-elementen stjäl från skärmen
            overhead_w = self.winfo_width() - self.chat_anchor_container.winfo_width()
            overhead_h = self.winfo_height() - self.chat_anchor_container.winfo_height()
            
            # Sätt programmets absoluta minimistorlek: Chattrutan (960x540) + övriga panelers pixlar
            min_window_w = 960 + max(0, overhead_w)
            min_window_h = 540 + max(0, overhead_h)
            self.minsize(min_window_w, min_window_h)

            # Hämta nuvarande tillgängliga utrymme för beräkning av 16:9-skalning uppåt
            container_w = self.chat_anchor_container.winfo_width()
            container_h = self.chat_anchor_container.winfo_height()
            
            if container_w <= 1 or container_h <= 1:
                return
                
            # Beräkna 16:9-mått utifrån tillgängligt utrymme med strikt flyttalsmatematik
            if container_w / container_h > 16.0 / 9.0:
                target_h = container_h
                target_w = int(container_h * (16.0 / 9.0))
            else:
                target_w = container_w
                target_h = int(container_w * (9.0 / 16.0))
                
            # Om uträkningen faller under basmåttet på grund av fönstertröghet, tvinga golvet
            if target_w < 960 or target_h < 540:
                target_w = 960
                target_h = 540
                
            # Låser ramens dimensioner stenhårt till 16:9 i övre vänstra hörnet utan fördröjning
            self.chat_anchor_surface.place_configure(width=target_w, height=target_h)

        # Bind storleksförändringar och kör en direkt rendering vid uppstart
        self.chat_anchor_container.bind("<Configure>", _enforce_16_9_aspect)
        self.update_idletasks()
        _enforce_16_9_aspect()
        
        self.model_monitor.start_lamp_monitor(
            core_hub_callback=lambda: self.core_hub,
            update_lamp_ui_callback=self._safe_update_lamp_color,
            get_switch_state_callback=lambda: self.ai_toggle_switch.get()
        )


```

==================================================
FILE: interface/gui_functions.py
TYPE: Kod
==================================================

```python
# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
- HÄMTAR FRÅN: Isolerade UI-händelser (Inga interna importberoenden mot presentation).
- ANROPAS AV: interface/client_gui.py
"""
import json
import os
import re
import threading
from functions.internet_functions import function_open_browser_link


def function_on_ai_toggle(gui_instance):
    """Dispatches dynamic tracking logs for the main AI engine switch."""
    if gui_instance.ai_toggle_switch.get() == 1:
        log_text = (
            gui_instance.localizer.get_text("log_ai_on")
            if gui_instance.localizer
            else "AI ON"
        )
        gui_instance.append_log("SYSTEM", log_text)
    else:
        log_text = (
            gui_instance.localizer.get_text("log_ai_off")
            if gui_instance.localizer
            else "AI OFF"
        )
        gui_instance.append_log("SYSTEM", log_text)
    function_sync_matrix_to_core(gui_instance)


def function_on_internet_toggle(gui_instance):
    """Handles the transactional state swap for the Internet AI capability block."""
    function_sync_matrix_to_core(gui_instance)


def function_sync_matrix_to_core(gui_instance):
    """Transactionally pushes localized switch values directly into the core matrix module."""
    if not gui_instance.matrix:
        return

    ch1 = True if gui_instance.chat_switch.get() == 1 else False
    ch2 = True if gui_instance.write_adapter_switch.get() == 1 else False
    ai_active = True if gui_instance.ai_toggle_switch.get() == 1 else False
    internet_active = True if gui_instance.internet_toggle.get() == 1 else False

    # INTEGRATION: Skicka det fjärde argumentet till ChannelMatrix för atomisk nätverksspärr
    gui_instance.matrix.update_states(
        ch1_chat=ch1,
        ch2_adapter=ch2,
        ai_active=ai_active,
        internet_active=internet_active,
    )

    if gui_instance.core_hub:
        gui_instance.core_hub.set_channels_state(ch1, ch2)


def function_on_telemetry_toggle(gui_instance):
    """Triggers the decoupled TelemetryCore worker loop based on widget state context and forces matrix sync."""
    if (
        not gui_instance.core_hub
        or not hasattr(gui_instance.core_hub, "telemetry_worker")
    ):
        return

    worker = gui_instance.core_hub.telemetry_worker

    if gui_instance.read_telemetry_switch.get() == 1:
        # Systemisk injektion: Om arbetartråden aldrig startats, plugga in våra callbacks nu
        if not worker.loop_active:

            def get_active_adapter():
                return getattr(gui_instance.core_hub, "active_adapter_instance", None)

            def telemetry_success_callback(data):
                if hasattr(gui_instance, "chat_window"):
                    gui_instance.chat_window.append_monitor_message(str(data))

            worker.start_polling_worker(
                current_adapter_callback=get_active_adapter,
                success_ui_callback=telemetry_success_callback,
            )

        worker.set_loop_state(True)
        log_text = (
            gui_instance.localizer.get_text("log_tel_on")
            if gui_instance.localizer
            else "Telemetry ON"
        )
        gui_instance.append_log("I/O-SIGNAL", log_text)
    else:
        worker.set_loop_state(False)
        log_text = (
            gui_instance.localizer.get_text("log_tel_off")
            if gui_instance.localizer
            else "Telemetry OFF"
        )
        gui_instance.append_log("I/O-SIGNAL", log_text)

    function_sync_matrix_to_core(gui_instance)


def function_on_lock_toggle(gui_instance):
    """Enforces safe keyboard barriers protecting peripheral data allocations inside HardwareIO."""
    if gui_instance.lock_switch.get() == 1:
        gui_instance.entry_field.configure(state="disabled")
        gui_instance.send_button.configure(state="disabled")
        gui_instance.append_log("SYSTEM", "Keyboard focus locked.")
        # INTEGRATION: Sätter flaggan i HardwareIO så att systemet vet att fysiska avbrott är spärrade
        if gui_instance.core_hub and hasattr(gui_instance.core_hub, "hardware"):
            gui_instance.core_hub.hardware.is_listening = False
    else:
        gui_instance.entry_field.configure(state="normal")
        gui_instance.send_button.configure(state="normal")
        gui_instance.append_log("SYSTEM", "Keyboard focus released.")
        # INTEGRATION: Återställer flaggan i HardwareIO till operationell status
        if gui_instance.core_hub and hasattr(gui_instance.core_hub, "hardware"):
            gui_instance.core_hub.hardware.is_listening = True


def function_on_model_change(gui_instance, selected_model):
    """Registers the modified cognitive targets inside global serialization tables on disk."""
    gui_instance.append_log("SYSTEM", f"Model changed to: {selected_model}")
    if gui_instance.core_hub and hasattr(gui_instance.core_hub, "ai_client"):
        gui_instance.core_hub.ai_client.model_name = selected_model
        gui_instance.core_hub.global_config["ai_model_name"] = selected_model
        try:
            with open(
                gui_instance.core_hub.config_path, "w", encoding="utf-8"
            ) as f:
                json.dump(
                    gui_instance.core_hub.global_config, f, indent=4
                )
        except Exception as e:
            print(f"[GUI-FUNCTION-ERROR] Failed to persist master config: {e}")


def function_on_adapter_change(gui_instance, selected_adapter):
    """Swaps dynamic pipeline references within central context containers cleanly."""
    no_adapter_text = (
        gui_instance.localizer.get_text("no_adapter")
        if gui_instance.localizer
        else "No Adapter Loaded"
    )
    if selected_adapter == no_adapter_text:
        gui_instance.boot_target_btn.configure(state="disabled")
        gui_instance.append_log("SYSTEM", "Adapter detached.")
        if gui_instance.core_hub:
            gui_instance.core_hub.unload_active_adapter()
    else:
        gui_instance.boot_target_btn.configure(state="normal")
        gui_instance.append_log(
            "SYSTEM", f"Adapter attached: {selected_adapter}"
        )
        if gui_instance.core_hub:
            gui_instance.core_hub.handle_adapter_switch(selected_adapter)


def function_trigger_text_input(gui_instance):
    """Relays local text streams to underlying cognitive pipelines asynchronously."""
    if gui_instance.lock_switch.get() == 1:
        return
    text = gui_instance.entry_field.get().strip()
    if not text:
        return
    gui_instance.entry_field.delete(0, "end")

    sender_tag = (
        "USER (Channel 1)"
        if gui_instance.chat_switch.get() == 1
        else "USER (Raw Stream)"
    )
    gui_instance.append_log(sender_tag, text)

    if gui_instance.core_hub:
        threading.Thread(
            target=gui_instance.core_hub.process_chatt_flow,
            args=(text,),
            daemon=True,
        ).start()


def function_handle_log_double_click(gui_instance, event):
    """Parses the current line under the mouse cursor to extract and open tagged URLs."""
    try:
        # Hämta exakt index för tecknet under muspekaren vid klicket
        click_index = gui_instance.log_box.index(f"@{event.x},{event.y}")

        # Kontrollera om tecknet har taggen "hyperlink" på sig
        tags = gui_instance.log_box.tag_names(click_index)

        if "hyperlink" in tags:
            # Hitta radnumret
            line_num = click_index.split(".")[0]

            # Hämta hela textraden
            full_line = gui_instance.log_box.get(
                f"{line_num}.0", f"{line_num}.end"
            ).strip()

            # Extrahera URL:en med Regex
            url_match = re.search(r"(https?://[^\s\)\}\]\",\']+)", full_line)
            if url_match:
                detected_url = url_match.group(1)
                # Skicka länken asynkront till standardwebbläsaren
                function_open_browser_link(detected_url)
    except Exception as e:
        print(f"[GUI-FUNCTION-ERROR] Link click parsing failed: {e}")

```

==================================================
FILE: interface/hardware_io.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: None (Strictly isolated hardware abstraction boundary).
 - CALLED BY: functons/bridge_functions.py, core/voice_core.py
"""
import keyboard
import time

class HardwareIO:
    def __init__(self):
        self.is_listening = False
        # Initialize the state flag directly to prevent AttributeError in concurrent threads
        self.key_released_event = False

    def normalize_key(self, raw_key: str) -> str:
        """Normalizes common Windows modifier key aliases for the keyboard hook system."""
        cleaned = str(raw_key).lower().strip()
        if cleaned in ["left ctrl", "right ctrl", "lctrl", "rctrl"]:
            return "ctrl"
        if cleaned in ["left shift", "right shift", "lshift", "rshift"]:
            return "shift"
        if cleaned in ["left alt", "right alt", "alt gr"]:
            return "alt"
        return cleaned

    def block_until_release(self, target_key: str, running_check_callback):
        """Monitors the key state smoothly without hijacking OS sound card buffers."""
        normalized = self.normalize_key(target_key)
        self.key_released_event = False
        
        try:
            # Active wait loop checking if the physical key is still depressed
            while keyboard.is_pressed(normalized) and running_check_callback():
                time.sleep(0.02)
            # Flip the transaction state flag to signal VoiceCore upon release
            self.key_released_event = True
        except Exception as e:
            print(f"[HARDWARE-ERROR] Key state release check faulted: {e}")
            self.key_released_event = True


```

==================================================
FILE: interface/ui_event_queue.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: Isolated system memory layout.
 - CALLED BY: main/main.py, interface/client_gui.py, and any background core thread.
"""

import queue
from typing import Callable

class UIEventQueue:
    def __init__(self):
        # Thread-safe FIFO queue for executing UI updates on the main execution thread
        self._queue = queue.Queue()

    def dispatch(self, callback: Callable[[], None]) -> None:
        """Enqueues a specific UI execution task from any background worker thread."""
        self._queue.put(callback)

    def process_next_batch(self) -> None:
        """Consumes all currently available thread tasks transactionally. Must be bound to gui.after()."""
        try:
            while True:
                callback = self._queue.get_nowait()
                try:
                    callback()
                except Exception as e:
                    print(f"[UI-QUEUE-ERROR] Failed to execute safe GUI callback function: {e}")
        except queue.Empty:
            pass


```

==================================================
FILE: interface/voice_core.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
CONNECTIONS:
- FETCHES FROM: interface/audio_io.py, interface/hardware_io.py, 
  core/localization_core.py
- CALLED BY: core/bridge_core.py, main/main.py
"""
import threading
import time

class VoiceCore:
    def __init__(self, audio_subsystem, hardware_subsystem):
        self.audio = audio_subsystem
        self.hardware = hardware_subsystem
        self.is_recording = False
        self._loop_active = False

    def execute_ptt_transaction(self, target_key, running_check_callback, 
                               success_callback, current_mode_callback):
        """Asynchronously orchestrates a clean voice interaction cycle supporting 
        both PTT and iterative LISTEN loops."""
        if self.is_recording:
            return
        self.is_recording = True

        def worker():
            try:
                # FIXED: Shifted from dangerous recursive calling to a flat, safe iterative while-loop
                while running_check_callback():
                    active_mode = str(current_mode_callback()).upper()

                    # Context A: If Push-To-Talk, launch the hardware block until the physical key is released
                    if active_mode == "PTT":
                        release_thread = threading.Thread(
                            target=self.hardware.block_until_release, 
                            args=(target_key, running_check_callback), 
                            daemon=True
                        )
                        release_thread.start()

                    # Open the audio hardware vector and capture human speech tokens
                    captured_text = ""
                    if self.audio:
                        captured_text = self.audio.listen()

                    # Synchronize and ensure the hotkey is released if we were in PTT mode
                    if active_mode == "PTT":
                        while not self.hardware.key_released_event and running_check_callback():
                            # SÄKERHETSSPÄRR: Om läget ändras i GUI under pågående väntan, bryt omedelbart
                            if str(current_mode_callback()).upper() != "PTT":
                                break
                            time.sleep(0.02)

                    # Dispatch the finalized tokens transactionally to the core bridge pipeline
                    if captured_text and captured_text.strip():
                        success_callback(captured_text)

                    # Context B: Continuous Iterative Listen Loop Check
                    # Supports both English (LISTEN) and Swedish (LYSSNA) localized tokens cleanly
                    if active_mode in ["LISTEN", "LYSSNA"] and running_check_callback():
                        time.sleep(0.3) # Give the soundcard hardware buffer a brief moment to settle
                        continue # Iterate cleanly on the same thread without stack leakage
                    else:
                        break # Terminate worker thread execution if mode has changed

            except Exception as e:
                print(f"[VOICE-CORE-ERROR] Asynchronous voice transaction failed: {e}")
            finally:
                self.is_recording = False

        threading.Thread(target=worker, daemon=True).start()

```

==================================================
FILE: main/main.py
TYPE: Kod
==================================================

```python
﻿# -*- coding: utf-8 -*-
"""
G.A.M.E. B.R.I.D.G.E. - Main Entry Point

KOPPLINGAR:
 - HÄMTAR FRÅN:
     - core.path_core.py
     - functions/bridge_functions.py
     - interface/client_gui.py
     - core/io_layer.py
     - core/session_manager.py
     - core/channel_matrix.py
     - interface/voice_core.py
     - core/localization_core.py
     - core/telemetry_core.py

 - ANROPAS AV:
     - Direkt terminalexekvering
     - Startskript från valfri katalog

ANSVAR:
 - Förankra projektroten.
 - Ladda lokal miljökonfiguration före övrig applikationsstart.
 - Initiera GameBridges centrala subsystems.
 - Starta GUI och applikationslivscykel.

SÄKERHET:
 - API-nycklar lagras inte i källkoden.
 - .env är lokal konfiguration och ska inte committas.
"""

import os
import sys


# ============================================================================
# 1. PROJEKTROT
# ============================================================================

_CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

_PROJECT_ROOT = os.path.dirname(
    _CURRENT_DIR
)

# Säkerställ att projektets rot alltid finns i Python-sökvägen.
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# ============================================================================
# 2. LOKAL MILJÖKONFIGURATION
# ============================================================================

def _load_local_env():
    """
    Läser projektets lokala .env-fil utan externa Python-beroenden.

    Endast enkla KEY=VALUE-rader används.

    Exempel:

        TAVILY_API_KEY=tvly-xxxxxxxx

    Kommentarer som börjar med '#' ignoreras.

    Befintliga systemmiljövariabler skrivs INTE över.
    Detta gör att en riktig systemvariabel alltid har företräde
    framför .env.

    .env ska aldrig committas till Git.
    """

    env_path = os.path.join(
        _PROJECT_ROOT,
        ".env"
    )

    if not os.path.isfile(env_path):
        print(
            "[SYSTEM] Ingen lokal .env hittades. "
            "Miljövariabler används som de är."
        )
        return

    loaded = 0

    try:
        with open(
            env_path,
            "r",
            encoding="utf-8"
        ) as env_file:

            for raw_line in env_file:
                line = raw_line.strip()

                # Tom rad.
                if not line:
                    continue

                # Kommentar.
                if line.startswith("#"):
                    continue

                # Acceptera även "export KEY=value".
                if line.startswith("export "):
                    line = line[7:].strip()

                if "=" not in line:
                    continue

                key, value = line.split(
                    "=",
                    1
                )

                key = key.strip()
                value = value.strip()

                if not key:
                    continue

                # Ta bort enkla eller dubbla citattecken runt värdet.
                if (
                    len(value) >= 2
                    and value[0] == value[-1]
                    and value[0] in ("'", '"')
                ):
                    value = value[1:-1]

                # Systemmiljövariabler har företräde.
                if key not in os.environ:
                    os.environ[key] = value
                    loaded += 1

        print(
            f"[SYSTEM] Lokal .env laddad: "
            f"{loaded} variabel/variabler."
        )

    except Exception as exc:
        # Ett problem med .env får inte förhindra att
        # GameBridge startar i övrigt.
        print(
            f"[SYSTEM-WARNING] Kunde inte läsa .env: {exc}"
        )


# Ladda .env NU, innan framework-modulerna importeras.
_load_local_env()


# ============================================================================
# 3. GAMEBRIDGE CORE IMPORTS
# ============================================================================

from core.path_core import PathCore

from functions.bridge_functions import GameBridgeCore

from interface.client_gui import GameBridgeGUI

from core.io_layer import GameBridgeIOLayer
from core.session_manager import SessionManager
from core.channel_matrix import ChannelMatrix
from interface.voice_core import VoiceCore
from core.localization_core import LocalizationCore
from core.telemetry_core import TelemetryCore


# ============================================================================
# 4. APPLICATION START
# ============================================================================

def main():
    # Production platform baseline v3.5.0
    print(
        "=== G.A.M.E. B.R.I.D.G.E. "
        "v3.5.0 PLATFORM PRODUCTION BASE ==="
    )

    print(
        "[SYSTEM] Application successfully anchored "
        f"to global root: {PathCore.PROJECT_ROOT}"
    )

    # ------------------------------------------------------------------------
    # Centraliserad core-infrastruktur
    # ------------------------------------------------------------------------

    localizer = LocalizationCore()

    io_layer = GameBridgeIOLayer()

    session_manager = SessionManager()

    matrix = ChannelMatrix()

    # ------------------------------------------------------------------------
    # Asynkron telemetry
    # ------------------------------------------------------------------------

    telemetry_worker = TelemetryCore(
        io_layer=io_layer
    )

    # ------------------------------------------------------------------------
    # Core hub
    # ------------------------------------------------------------------------

    core = GameBridgeCore()

    core.matrix = matrix
    core.io_layer = io_layer
    core.localizer = localizer
    core.telemetry_worker = telemetry_worker

    # ------------------------------------------------------------------------
    # Voice subsystem
    # ------------------------------------------------------------------------

    voice = VoiceCore(
        audio_subsystem=core.audio,
        hardware_subsystem=core.hardware
    )

    core.voice = voice

    # ------------------------------------------------------------------------
    # GUI
    # ------------------------------------------------------------------------

    gui = GameBridgeGUI(
        core_hub=core,
        matrix=matrix,
        localizer=localizer
    )

    # ------------------------------------------------------------------------
    # Cross-link asynchronous communication channels
    # ------------------------------------------------------------------------

    io_layer.register_ui_channel(
        gui.append_log
    )

    core.link_gui(gui)

    # Fire off hardware keyboard vectors and voice confirmation
    # strictly ONCE here.
    core.boot_platform_loops()

    print(
        "[SYSTEM] All decoupled sub-cores successfully mapped "
        "and injected. Launching GUI..."
    )

    # ------------------------------------------------------------------------
    # GUI lifecycle
    # ------------------------------------------------------------------------

    try:
        gui.mainloop()

    except KeyboardInterrupt:
        print(
            "[SYSTEM] Execution interrupted by user. "
            "Flushing memory buffers clean."
        )

    except Exception as exc:
        print(
            "[SYSTEM-NOTIFY] "
            f"Application lifecycle safely terminated: {exc}"
        )


# ============================================================================
# 5. DIRECT EXECUTION
# ============================================================================

if __name__ == "__main__":
    main()

```

==================================================
FILE: plugins/notepad_plugin/main_adapter.py
TYPE: Kod
==================================================

```python
# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
  - HÄMTAR FRÅN: adapters.base_adapter, core.path_core
  - ANROPAS AV: adapters.adapter_loader (Dynamisk plugin-skanner under runtime)
"""

import os
import json
import subprocess
import time
import ctypes
from typing import Any
from adapters.base_adapter import BaseAdapter
from core.path_core import PathCore

try:
    import pyautogui
    pyautogui.FAILSAFE = True 
except ImportError:
    pyautogui = None

class NotepadAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        # Exposed publicly for dynamic frame loader recognition
        self.adapter_name = "Notepad++ (Target X)"
        # FIXED: Relies entirely on PathCore to map the absolute location dynamically
        self.config_path = PathCore.get_adapter_file("notepad_plugin", "plugin_config.json")
        self.target_path = "C:\\Program Files\\Notepad\\notepad++.exe"
        
    def initialize(self):
        """Initializes settings and safely extracts local application executables paths."""
        print(f"[{self.adapter_name}] Initializing reference extension...")
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.target_path = config.get("target_path", self.target_path)
            except Exception as e:
                print(f"[{self.adapter_name}] Configuration processing failure: {e}")

    def boot_or_attach(self):
        """Validates host processes to either connect or spawn a clean execution lifecycle."""
        print(f"[{self.adapter_name}] Evaluating external process lifecycle states...")
        try:
            output = subprocess.check_output('tasklist', shell=True).decode('cp1252', errors='ignore')
            if "notepad++.exe" in output.lower():
                print(f"[{self.adapter_name}] Target process identified as active. Attached to live memory environment.")
                return
        except Exception:
            pass
            
        if os.path.exists(self.target_path):
            print(f"[{self.adapter_name}] Spawning executable instance: {self.target_path}")
            try:
                subprocess.Popen(self.target_path)
                time.sleep(1.5)
            except Exception as e:
                print(f"[{self.adapter_name}] Failed to establish executable frame: {e}")

    def get_capabilities(self) -> dict:
        """Reports automation constraints and system actions dynamically to cognitive layers."""
        return {
            "interaction_type": "active_gui_automation",
            "io_tool": "PyAutoGUI",
            "requires_window_focus": True,
            "supported_actions": ["write_text_cleartext", "simulate_keystrokes"],
            "limitations": "Incapable of dispatching silent or background virtual hardware calls."
        }

    def _focus_target_window(self):
        """Queries local Windows kernel mappings to force screen layer focus."""
        try:
            hwnd = ctypes.windll.user32.FindWindowW(ctypes.c_wchar_p("Notepad++"), None)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                time.sleep(0.1)
                return True
        except Exception:
            pass
        return False

    def read_telemetry(self) -> dict:
        """Extracts runtime environmental properties back into structural system arrays."""
        return {
            "application": "Notepad++",
            "status": "connected",
            "current_context": "Raw text automation frame for physical I/O verification metrics.",
            "timestamp": time.time()
        }

    def execute_interaction(self, action_data: Any):
        """Channel 2 Target: Decodes and drives input parameters directly into the window layer."""
        if not action_data or (isinstance(action_data, str) and "[AI-API-ERROR]" in action_data):
            return
            
        print(f"[{self.adapter_name}] Channel 2 routing execution payload processing...")
        
        intent_map = {}
        if isinstance(action_data, str):
            cleaned_data = action_data.strip()
            if cleaned_data.startswith("{") and cleaned_data.endswith("}"):
                try:
                    intent_map = json.loads(cleaned_data)
                except Exception:
                    pass
        elif isinstance(action_data, dict):
            intent_map = action_data

        clean_text_to_type = ""
        if intent_map:
            clean_text_to_type = intent_map.get("text", "")
            if not clean_text_to_type:
                clean_text_to_type = intent_map.get("command", "")
            
            payload = intent_map.get("payload", {})
            if isinstance(payload, dict):
                decision = payload.get("decision", "")
                if decision:
                    clean_text_to_type = decision

        if not clean_text_to_type and isinstance(action_data, str):
            clean_text_to_type = action_data

        if pyautogui and clean_text_to_type:
            try:
                self._focus_target_window()
                pyautogui.write(f"\n{clean_text_to_type}", interval=0.01)
            except Exception as e:
                print(f"[{self.adapter_name}] PyAutoGUI continuous automated typing exception: {e}")

    def shutdown(self):
        """Flushes local link vectors and disconnects active window focus threads."""
        print(f"[{self.adapter_name}] Safely disconnected automation pipeline hooks.")

```

==================================================
FILE: providers/tavily_provider.py
TYPE: Kod
==================================================

```python
# `providers/tavily_provider.py`

# -*- coding: utf-8 -*-
"""
GameBridge Tavily Provider


KOPPLINGAR:
 - ANROPAS AV:
     - ai.internet_transport.InternetTransport
 - HÄMTAR FRÅN:
     - Tavily Search API

ANSVAR:
 - Endast Tavily-specifik kommunikation.
 - Läsa TAVILY_API_KEY från miljö.
 - Skicka query via HTTPS.
 - Normalisera Tavily-resultat till GameBridges generella format.

Providerlagret ska inte innehålla:
 - GUI-logik
 - routerlogik
 - AI-persona
 - prompt-instruktioner
 - Ejecta-specifik logik
"""

import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlparse


class TavilyProvider:
    """Tavily implementation av GameBridges sökprovider-kontrakt."""

    name = "tavily"

    API_ENDPOINT = "https://api.tavily.com/search"

    def __init__(self, timeout=8.0):
        self.timeout = float(timeout)
        self.api_key = self._load_api_key()

    @staticmethod
    def _load_api_key() -> str:
        """
        Hämtar TAVILY_API_KEY från miljön.

        GameBridge förutsätter att startmiljön laddar .env,
        eller att TAVILY_API_KEY redan finns som miljövariabel.

        Nyckeln skrivs aldrig ut eller loggas.
        """

        return os.environ.get(
            "TAVILY_API_KEY",
            ""
        ).strip()

    def search(self, query: str) -> dict:
        """Utför en Tavily-sökning."""

        query = (query or "").strip()

        if not query:
            return self._failure(
                query,
                "Ingen sökfråga angiven."
            )

        if not self.api_key:
            return self._failure(
                query,
                "TAVILY_API_KEY saknas."
            )

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": 3
        }

        request_data = json.dumps(
            payload,
            ensure_ascii=False
        ).encode("utf-8")

        request = urllib.request.Request(
            self.API_ENDPOINT,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "GameBridge/1.0"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout
            ) as response:

                raw_response = response.read().decode(
                    "utf-8",
                    errors="replace"
                )

                status_code = response.status

            if status_code < 200 or status_code >= 300:
                return self._failure(
                    query,
                    f"Tavily returnerade HTTP {status_code}."
                )

            data = json.loads(raw_response)

            normalized_results = []

            for item in data.get(
                "results",
                []
            )[:3]:

                url = str(
                    item.get("url", "")
                ).strip()

                normalized_results.append(
                    {
                        "title": str(
                            item.get(
                                "title",
                                ""
                            )
                        ),
                        "content": str(
                            item.get(
                                "content",
                                ""
                            )
                        ),
                        "url": url,
                        "domain": self._extract_domain(
                            url
                        )
                    }
                )

            return {
                "success": True,
                "provider": self.name,
                "query": query,
                "results": normalized_results,
                "error": None
            }

        except urllib.error.HTTPError as exc:
            error_body = ""

            try:
                error_body = exc.read().decode(
                    "utf-8",
                    errors="replace"
                )
            except Exception:
                pass

            print(
                "\n=== [TAVILY HTTP ERROR] ==="
            )
            print(f"HTTP status: {exc.code}")

            if error_body:
                print(
                    f"Server response: "
                    f"{error_body[:1000]}"
                )

            print(
                "============================\n"
            )

            return self._failure(
                query,
                f"Tavily HTTP {exc.code}."
            )

        except urllib.error.URLError as exc:
            return self._failure(
                query,
                f"Nätverksfel: {exc.reason}"
            )

        except json.JSONDecodeError:
            return self._failure(
                query,
                "Tavily returnerade ogiltig JSON."
            )

        except TimeoutError:
            return self._failure(
                query,
                "Tavily-förfrågan tog för lång tid."
            )

        except Exception as exc:
            return self._failure(
                query,
                f"{type(exc).__name__}: {exc}"
            )

    def _failure(
        self,
        query: str,
        error: str
    ) -> dict:
        """Returnerar ett konsekvent providerfel."""

        return {
            "success": False,
            "provider": self.name,
            "query": query,
            "results": [],
            "error": error
        }

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Returnerar normaliserad domän från URL."""

        if not url:
            return ""

        try:
            parsed = urlparse(url)

            domain = (
                parsed.netloc
                or ""
            ).lower()

            if domain.startswith("www."):
                domain = domain[4:]

            return domain

        except Exception:
            return ""

```
