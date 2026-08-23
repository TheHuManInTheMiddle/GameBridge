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