# -*- coding: utf-8 -*-
"""
GameBridge Internet Transport

KOPPLINGAR:
 - HÄMTAR FRÅN:
     - core.path_core.PathCore
     - extern provider från providers/

 - ANROPAS AV:
     - core.cognitive_router_core

ANSVAR:
 - GameBridges befintliga internet-accesspunkt.
 - Dynamiskt hitta extern provider från providers/.
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
       providers/
            |
            v
    första giltiga provider
            |
            v
        externt API

VIKTIGT:
 - InternetTransport är den enda internet-accesspunkten
   som cognitive_router_core behöver känna till.
 - Providerfilens namn är inte hårdkodat.
 - Providerfiler ligger utanför den paketerade kärnan.
 - Rått provider-JSON skickas ALDRIG direkt till Channel 1.
 - InternetTransport återställer GameBridges tidigare
   {"response": "...", "link": "..."}-kontrakt.
"""

import importlib.util
import inspect
import json
import os
from datetime import datetime, timezone

from core.path_core import PathCore


class InternetTransport:
    """
    GameBridges stabila internet-accesspunkt.

    Routern behöver inte känna till vilken provider
    som används under transportlagret.
    """

    def __init__(self, provider=None, timeout=8.0):
        self.timeout = float(timeout)

        # Provider kan injiceras för tester eller framtida
        # explicit provider-val.
        self.provider = provider or self._load_provider()

        self.enabled = True

        self.log_path = PathCore.get_internet_log_path()

    def _load_provider(self):
        """
        Hittar och laddar första giltiga Python-provider
        från den externa providers/-mappen.

        Filnamnet spelar ingen roll.

        En giltig provider måste:
        - vara en klass definierad i providerfilen
        - kunna instansieras
        - exponera en callable search(query)-metod
        """

        provider_root = PathCore.get_provider_root()

        if not os.path.isdir(provider_root):
            raise RuntimeError(
                f"Provider-mappen saknas: {provider_root}"
            )

        provider_files = sorted(
            filename
            for filename in os.listdir(provider_root)
            if (
                filename.endswith(".py")
                and filename != "__init__.py"
                and not filename.startswith("_")
            )
        )

        for filename in provider_files:

            file_path = os.path.join(
                provider_root,
                filename
            )

            module_name = (
                "gamebridge_provider_"
                + os.path.splitext(filename)[0]
            )

            try:
                spec = importlib.util.spec_from_file_location(
                    module_name,
                    file_path
                )

                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(
                    spec
                )

                spec.loader.exec_module(module)

                for _, candidate in inspect.getmembers(
                    module,
                    inspect.isclass
                ):

                    # Ignorera importerade klasser.
                    if candidate.__module__ != module.__name__:
                        continue

                    search_method = getattr(
                        candidate,
                        "search",
                        None
                    )

                    if not callable(search_method):
                        continue

                    try:
                        provider = candidate(
                            timeout=self.timeout
                        )

                    except TypeError:
                        # Tillåt även providers som inte använder
                        # timeout-argumentet i konstruktorn.
                        provider = candidate()

                    if callable(
                        getattr(
                            provider,
                            "search",
                            None
                        )
                    ):
                        print(
                            "[+] [INTERNET_TRANSPORT] "
                            f"Provider laddad: "
                            f"{getattr(provider, 'name', filename)}"
                        )

                        return provider

            except Exception as exc:
                print(
                    "[!] [INTERNET_TRANSPORT] "
                    f"Kunde inte ladda provider "
                    f"'{filename}': {exc}"
                )

        raise RuntimeError(
            "Ingen giltig internet-provider hittades "
            "i providers/."
        )

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
            # ----------------------------------------------------------
            # Provider-anrop
            # ----------------------------------------------------------

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
                    "error": (
                        "Providern returnerade "
                        "ett ogiltigt resultat."
                    )
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

            # ----------------------------------------------------------
            # Providerfel
            # ----------------------------------------------------------

            if not result.get("success", False):

                provider_error = result.get(
                    "error",
                    "Okänt providerfel."
                )

                return self._response(
                    response=(
                        f"[API-ERROR] Internetåtkomst "
                        f"misslyckades: {provider_error}"
                    ),
                    link=""
                )

            # ----------------------------------------------------------
            # Hämta resultat
            # ----------------------------------------------------------

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

            # ----------------------------------------------------------
            # Bygg rent mänskligt svar
            #
            # Rått provider-JSON får ALDRIG lämna transportlagret.
            # ----------------------------------------------------------

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