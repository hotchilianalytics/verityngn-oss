"""Shared fixtures for verityngn-mcp v2 tests: an in-process client and engine fakes."""

from __future__ import annotations

import base64
import datetime as dt
import json
import time
from typing import Any, Callable, Optional

import pytest

from verityngn.agent.mcp_v2.adapters import Adapters
from verityngn.agent.mcp_v2.adapters.disclosure import AssessRequest
from verityngn.agent.mcp_v2.config import ServerConfig
from verityngn.agent.mcp_v2.server import McpServer

VERSION = "2026-07-28"

TENK = """ITEM 1. BUSINESS
Example Corp builds software.
ITEM 1A. RISK FACTORS
Risks Relating to Cybersecurity. We may experience cybersecurity incidents that could materially adversely affect our business and reputation.
Risks Relating to Liquidity. Our credit facility contains covenants that may restrict our operations.
ITEM 1B. UNRESOLVED STAFF COMMENTS
None.
ITEM 2. PROPERTIES
We lease offices in Redmond.
"""
HEDGED = "We may experience cybersecurity incidents"

VTT = """WEBVTT

00:00:01.000 --> 00:00:04.000
Welcome to our quarterly update.

00:00:05.000 --> 00:00:09.000
Our systems have never been breached by any attacker.

00:00:10.000 --> 00:00:14.000
We expect revenue to grow next year.
"""


class FakeDisclosure:
    """Test-only engine: pairs the hedged Item 1A sentence with a dated 8-K quote."""

    name = "fake-rfkit"
    version = "0.0-test"

    def __init__(self, delay: float = 0.0) -> None:
        self.delay = delay
        self.calls: list[AssessRequest] = []

    def assess(self, request: AssessRequest, progress: Callable[[str], None]) -> list[dict[str, Any]]:
        self.calls.append(request)
        steps = int(self.delay / 0.05) if self.delay else 0
        for i in range(steps):
            progress(f"step {i}")
            time.sleep(0.05)
        idx = request.text.find(HEDGED, request.start, request.end)
        out = []
        if idx >= 0:
            out.append(
                {
                    "claim_text": request.text[idx:idx + len(HEDGED)],
                    "start": idx,
                    "end": idx + len(HEDGED),
                    "claim_kind": "disclosure_pair",
                    "verdict_or_action": "REWRITE",
                    "category": "cybersecurity",
                    "item_1a_heading": "Risks Relating to Cybersecurity",
                    "confidence": 0.8,
                    "illustrative_rewrite": "We have experienced cybersecurity incidents, including ...",
                    "lag_clock": {"event_date": "2024-01-12", "filing_date": "2024-07-30", "days": 200},
                    "evidence": [
                        {
                            "source": "EXMP 8-K Item 1.05",
                            "quote": "On January 12, 2024, the Company detected a nation-state attack on its corporate systems.",
                            "date": "2024-01-19",
                            "url": "https://www.sec.gov/Archives/edgar/data/1/000000000024000001/x8k.htm",
                            "source_id": "0000000000-24-000001+1.05",
                            "source_class": "own",
                            "stance": "contradicts_disclosure",
                        },
                        {
                            "source": "Short report",
                            "quote": "The company hid a breach.",
                            "date": "2024-02-01",
                            "url": "https://hindenburgresearch.com/example",
                            "source_class": "short",
                            "stance": "supports_exposure",
                        },
                    ],
                }
            )
        return out


class FakeVideo:
    name = "fake-verityngn"
    version = "0.0-test"

    def __init__(self, delay: float = 0.0) -> None:
        self.delay = delay

    def analyze(self, video_id: str, *, tier: str, domain_pack: str, progress: Callable[[str], None]) -> dict[str, Any]:
        progress("transcribing")
        if self.delay:
            time.sleep(self.delay)
        progress("extracting claims")
        return {
            "vtt": VTT,
            "claims": [
                {"claim_text": "Our systems have never been breached by any attacker.", "start_s": 6.0},
                {"claim_text": "We expect revenue to grow next year.", "start_s": 11.0, "claim_kind": "prediction"},
            ],
            "model": "gemini-test",
        }


class FakeEdgar:
    def resolve(self, *, name: str = "", ticker: str = "", cik: str = "", limit: int = 5) -> list[dict[str, Any]]:
        if ticker.upper() == "EXMP" or cik in ("1", "0000000001") or name.lower().startswith("example"):
            return [{"cik": "1", "name": "EXAMPLE CORP", "tickers": ["EXMP"]}]
        return []

    def aliases(self, cik: str) -> list[str]:
        return ["EXAMPLE SOFTWARE INC"]

    def last_10k(self, cik: str) -> Optional[dt.date]:
        return dt.date.today() - dt.timedelta(days=120)

    def filings(self, cik, forms, start, end, items=None):
        return [{"accession": "0000000000-24-000001", "form": "8-K", "items": ["1.05"], "filed_at": "2024-01-19",
                 "url": "https://www.sec.gov/Archives/edgar/data/1/000000000024000001/x8k.htm", "source_class": "own"}]

    def full_text(self, cik, query, forms, start, end, items=None):
        return self.filings(cik, forms, start, end, items)


class FakeChannels:
    def channels(self, cik: Optional[str]) -> list[dict[str, Any]]:
        if cik and int(cik) == 1:
            return [{"platform": "youtube", "channel_id": "UCexampleOwned000000000", "verified_by": "issuer_site_link"}]
        return []


class FakeYouTube:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def uploads(self, channel_id, start, end, max_results):
        self.calls.append(channel_id)
        return [{"video_id": "abcdefghijk", "channel_id": channel_id, "title": "Q3 update", "published_at": end.isoformat() + "T12:00:00Z"}]

    def published_date(self, video_id: str) -> Optional[str]:
        return "2026-09-30"


class FakeNews:
    name = "gdelt"

    def __init__(self, available: bool = False) -> None:
        self._available = available

    def available(self, licences) -> bool:
        return self._available

    @staticmethod
    def covers(start, today) -> bool:
        return (today - start).days <= 92

    def search(self, entity_name, start, end, query, langs, limit):
        return [{"uri": "https://news.example.com/a", "headline": f"{entity_name} update", "source": "news.example.com",
                 "date": end.isoformat(), "url": "https://news.example.com/a", "allegation": False}]


class FakeSanctions:
    def match(self, name, schema, country="", birth_date="", limit=10):
        return [{"opensanctions_id": "Q1", "caption": name, "score": 0.91, "datasets": ["us_ofac_sdn"],
                 "url": "https://www.opensanctions.org/entities/Q1/"}]


def fake_adapters(**overrides: Any) -> Adapters:
    news = FakeNews()
    parts = dict(
        disclosure=FakeDisclosure(),
        video=FakeVideo(),
        edgar=FakeEdgar(),
        youtube=FakeYouTube(),
        channels=FakeChannels(),
        event_registry=FakeNews(available=False),
        gdelt=news,
        sanctions=FakeSanctions(),
    )
    parts.update(overrides)
    return Adapters(**parts)


class Client:
    def __init__(self, server: McpServer) -> None:
        self.server = server
        self._id = 0

    def raw(self, method: str, params: Optional[dict[str, Any]] = None, *, token: Optional[str] = "dev:acme:analyst",
            tasks: bool = False, headers: Optional[dict[str, str]] = None, http_method: str = "POST",
            path: str = "/mcp", notification: bool = False, b64_name: bool = False):
        self._id += 1
        params = dict(params or {})
        caps: dict[str, Any] = {"extensions": {"io.modelcontextprotocol/tasks": {}}} if tasks else {}
        params["_meta"] = {
            "io.modelcontextprotocol/protocolVersion": VERSION,
            "io.modelcontextprotocol/clientCapabilities": caps,
            "io.modelcontextprotocol/clientInfo": {"name": "pytest", "version": "1"},
        }
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
             "MCP-Protocol-Version": VERSION, "Mcp-Method": method}
        if method in ("tools/call", "prompts/get"):
            h["Mcp-Name"] = params["name"]
        if method == "resources/read":
            h["Mcp-Name"] = params["uri"]
        if b64_name and "Mcp-Name" in h:
            h["Mcp-Name"] = "=?base64?" + base64.b64encode(h["Mcp-Name"].encode()).decode() + "?="
        if token:
            h["Authorization"] = f"Bearer {token}"
        h.update(headers or {})
        body: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "params": params}
        if not notification:
            body["id"] = self._id
        resp = self.server.handle_http(http_method, path, h, json.dumps(body).encode())
        payload = json.loads(resp.body) if resp.body else None
        return resp, payload

    def rpc(self, method: str, params: Optional[dict[str, Any]] = None, **kw: Any) -> dict[str, Any]:
        resp, payload = self.raw(method, params, **kw)
        assert resp.status == 200, (resp.status, payload)
        assert "result" in payload, payload
        return payload["result"]

    def tool(self, name: str, arguments: dict[str, Any], **kw: Any) -> dict[str, Any]:
        return self.rpc("tools/call", {"name": name, "arguments": arguments}, **kw)

    def ok(self, name: str, arguments: dict[str, Any], **kw: Any) -> dict[str, Any]:
        res = self.tool(name, arguments, **kw)
        assert not res.get("isError"), res
        return res["structuredContent"]

    def err(self, name: str, arguments: dict[str, Any], **kw: Any) -> dict[str, Any]:
        res = self.tool(name, arguments, **kw)
        assert res.get("isError") is True, res
        return res["structuredContent"]

    def wait_task(self, task_id: str, *, token: str = "dev:acme:analyst", timeout: float = 10.0, until=("completed", "failed", "cancelled")) -> dict[str, Any]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            res = self.rpc("tasks/get", {"taskId": task_id}, token=token, tasks=True)
            if res["status"] in until:
                return res
            time.sleep(0.05)
        raise AssertionError(f"task {task_id} did not reach {until}")

    def wait_report(self, report_id: str, *, token: str = "dev:acme:analyst", timeout: float = 10.0) -> dict[str, Any]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            rep = self.ok("get_report", {"report_id": report_id}, token=token)
            if rep["status"] != "running":
                return rep
            time.sleep(0.05)
        raise AssertionError("report did not finish")


def make_server(adapters: Optional[Adapters] = None, **config: Any) -> McpServer:
    cfg = ServerConfig(dev_mode=True, authorization_servers=("https://auth.example.com",), **config)
    return McpServer(cfg, adapters=adapters or fake_adapters())


@pytest.fixture
def server() -> McpServer:
    return make_server()


@pytest.fixture
def client(server: McpServer) -> Client:
    return Client(server)


@pytest.fixture
def doc_id(client: Client) -> str:
    return client.ok("register_document", {"text": TENK, "media_type": "text/plain", "rights": "public_source"})["doc_id"]


def output_valid(name: str, structured: Any) -> None:
    from verityngn.agent.mcp_v2.tools import output_errors

    problems = output_errors(name, structured)
    assert not problems, problems
