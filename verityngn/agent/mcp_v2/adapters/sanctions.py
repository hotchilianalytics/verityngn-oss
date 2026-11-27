"""OpenSanctions ``/match`` adapter. Results are candidates, never determinations."""

from __future__ import annotations

import os
from typing import Any, Optional

from verityngn.agent.mcp_v2.adapters.http import request_json
from verityngn.agent.mcp_v2.errors import ToolFailure

LABEL = "Candidates for human review, not determinations"


class OpenSanctions:
    provider = "OpenSanctions"

    def __init__(self, api_key: Optional[str] = None, dataset: str = "default") -> None:
        self.api_key = api_key or os.environ.get("OPENSANCTIONS_API_KEY")
        self.dataset = dataset

    def match(self, name: str, schema: str, country: str = "", birth_date: str = "", limit: int = 10) -> list[dict[str, Any]]:
        if not self.api_key:
            raise ToolFailure(
                "UPSTREAM",
                "Sanctions screening is not configured on this server (no OpenSanctions key).",
                alternative="Search the person or company by hand at https://www.opensanctions.org/ and attach what you find as evidence.",
            )
        props: dict[str, list[str]] = {"name": [name]}
        if country:
            props["country"] = [country]
        if birth_date and schema == "Person":
            props["birthDate"] = [birth_date]
        body = {"queries": {"q": {"schema": schema, "properties": props}}}
        data = request_json(
            f"https://api.opensanctions.org/match/{self.dataset}?limit={limit}",
            method="POST",
            body=body,
            headers={"Authorization": f"ApiKey {self.api_key}"},
            provider=self.provider,
        )
        results = ((data.get("responses") or {}).get("q") or {}).get("results") or []
        return [
            {
                "opensanctions_id": r.get("id", ""),
                "caption": r.get("caption", ""),
                "score": float(r.get("score") or 0.0),
                "datasets": list(r.get("datasets") or []),
                "url": f"https://www.opensanctions.org/entities/{r.get('id', '')}/",
            }
            for r in results
        ]
