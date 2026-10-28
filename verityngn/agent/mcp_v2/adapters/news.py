"""Directed news for one entity and one bounded window.

Event Registry is the default provider once a plan is on file; GDELT is used
only for windows inside the last three months. Short-seller publishers are
flagged as Allegation.
"""

from __future__ import annotations

import datetime as dt
import os
import urllib.parse
from typing import Any, Optional

from verityngn.agent.mcp_v2.adapters.http import request_json
from verityngn.agent.mcp_v2.errors import ToolFailure

GDELT_DAYS = 92
GDELT_ATTRIBUTION = "News index: The GDELT Project (https://www.gdeltproject.org/)"
ER_ATTRIBUTION = "News data: Event Registry (https://eventregistry.org/)"

# Fallback list until rfkit/sources/shorts.py's publisher list is installed.
SHORT_SELLER_DOMAINS = frozenset(
    {
        "hindenburgresearch.com",
        "muddywatersresearch.com",
        "citronresearch.com",
        "sprucepointcap.com",
        "kerrisdalecap.com",
        "wolfpackresearch.com",
        "culperresearch.com",
        "fuzzypandaresearch.com",
        "grizzlyreports.com",
        "jcapitalresearch.com",
        "gothamcityresearch.com",
        "viceroyresearch.org",
        "bonitasresearch.com",
        "iceberg-research.com",
        "scorpioncapital.com",
        "bleeckerstreetresearch.com",
    }
)


def is_allegation(url_or_domain: str) -> bool:
    host = urllib.parse.urlparse(url_or_domain).hostname or url_or_domain
    host = host.lower().removeprefix("www.")
    return any(host == d or host.endswith("." + d) for d in SHORT_SELLER_DOMAINS)


class EventRegistryNews:
    name = "event_registry"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("EVENT_REGISTRY_API_KEY")

    def available(self, licences: tuple[str, ...]) -> bool:
        return bool(self.api_key) or "event_registry" in licences

    def search(self, entity_name: str, start: dt.date, end: dt.date, query: str, langs: list[str], limit: int) -> list[dict[str, Any]]:
        if not self.api_key:
            raise ToolFailure(
                "UPSTREAM",
                "Event Registry is not configured on this server.",
                alternative="Narrow the window to the last three months to use GDELT, or ask an admin to add the Event Registry key.",
            )
        body = {
            "action": "getArticles",
            "keyword": [entity_name] + ([query] if query else []),
            "keywordOper": "and",
            "lang": langs,
            "dateStart": start.isoformat(),
            "dateEnd": end.isoformat(),
            "articlesCount": min(limit, 100),
            "articlesSortBy": "date",
            "resultType": "articles",
            "apiKey": self.api_key,
        }
        data = request_json(
            "https://eventregistry.org/api/v1/article/getArticles", method="POST", body=body, provider="Event Registry"
        )
        out = []
        for art in ((data.get("articles") or {}).get("results")) or []:
            url = art.get("url", "")
            out.append(
                {
                    "uri": str(art.get("uri") or url),
                    "headline": art.get("title", ""),
                    "source": (art.get("source") or {}).get("title") or (art.get("source") or {}).get("uri", ""),
                    "date": str(art.get("date") or art.get("dateTime", ""))[:10],
                    "excerpt": (art.get("body") or "")[:400],
                    "url": url,
                    "allegation": is_allegation(url),
                }
            )
        return out


class GdeltNews:
    name = "gdelt"

    @staticmethod
    def covers(start: dt.date, today: dt.date) -> bool:
        return (today - start).days <= GDELT_DAYS

    def search(self, entity_name: str, start: dt.date, end: dt.date, query: str, langs: list[str], limit: int) -> list[dict[str, Any]]:
        terms = [f'"{entity_name}"' if " " in entity_name else entity_name]
        if query:
            terms.append(f'"{query}"' if " " in query else query)
        if langs == ["eng"]:
            terms.append("sourcelang:english")
        params = {
            "query": " ".join(terms),
            "mode": "artlist",
            "format": "json",
            "maxrecords": min(limit, 250),
            "sort": "datedesc",
            "startdatetime": start.strftime("%Y%m%d") + "000000",
            "enddatetime": end.strftime("%Y%m%d") + "235959",
        }
        data = request_json("https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode(params), provider="GDELT")
        out = []
        for art in data.get("articles") or []:
            seen = str(art.get("seendate", ""))
            day = f"{seen[0:4]}-{seen[4:6]}-{seen[6:8]}" if len(seen) >= 8 else ""
            url = art.get("url", "")
            out.append(
                {
                    "uri": url,
                    "headline": art.get("title", ""),
                    "source": art.get("domain", ""),
                    "date": day,
                    "url": url,
                    "allegation": is_allegation(url),
                }
            )
        return out[:limit]
