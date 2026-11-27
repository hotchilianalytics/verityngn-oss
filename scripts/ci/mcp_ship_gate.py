#!/usr/bin/env python3
"""MCP ship gate: assert real tool results, not command strings.

Starts verityngn-mcp v2 on loopback with the real engine adapters, calls tools
over Streamable HTTP, and validates every result against its outputSchema.
Each check reports REAL (a validated result), BLOCKED (the engine or provider
is not installed or configured here; reported honestly, never faked) or FAIL.
The 3.1 stdio server is reported separately as a command surface, never as
execution.

    python scripts/ci/mcp_ship_gate.py            # offline checks
    python scripts/ci/mcp_ship_gate.py --live     # adds SEC EDGAR round trips

Exit code is 1 if any check FAILs.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from verityngn.agent.mcp_v2.config import ServerConfig  # noqa: E402
from verityngn.agent.mcp_v2.server import McpServer  # noqa: E402
from verityngn.agent.mcp_v2.tools import output_errors  # noqa: E402
from verityngn.agent.mcp_v2.transport import serve_in_thread  # noqa: E402

VERSION = "2026-07-28"
BLOCKING_CODES = {"ENGINE_NOT_INSTALLED", "UPSTREAM"}
FIXTURE = (
    "ITEM 1A. RISK FACTORS\n"
    "Risks Relating to Cybersecurity. We may experience cybersecurity incidents that could materially "
    "adversely affect our business.\nITEM 1B. UNRESOLVED STAFF COMMENTS\nNone.\n"
)


class Gate:
    def __init__(self, base: str) -> None:
        self.base = base
        self.rows: list[tuple[str, str, str]] = []
        self._id = 0

    def post(self, method: str, params: dict[str, Any] | None = None, *, token: str | None = "dev:gate:analyst", tasks: bool = False) -> tuple[int, dict[str, Any]]:
        self._id += 1
        params = dict(params or {})
        caps = {"extensions": {"io.modelcontextprotocol/tasks": {}}} if tasks else {}
        params["_meta"] = {"io.modelcontextprotocol/protocolVersion": VERSION, "io.modelcontextprotocol/clientCapabilities": caps}
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                   "MCP-Protocol-Version": VERSION, "Mcp-Method": method}
        if method == "tools/call":
            headers["Mcp-Name"] = params["name"]
        if token:
            headers["Authorization"] = f"Bearer {token}"
        body = json.dumps({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}).encode()
        req = urllib.request.Request(self.base + "/mcp", data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read() or b"{}")

    def record(self, name: str, status: str, detail: str) -> None:
        self.rows.append((name, status, detail))

    def tool(self, name: str, arguments: dict[str, Any], *, check=None, token: str = "dev:gate:analyst") -> dict[str, Any] | None:
        status, body = self.post("tools/call", {"name": name, "arguments": arguments}, token=token, tasks=True)
        if status != 200 or "result" not in body:
            self.record(name, "FAIL", f"HTTP {status}: {body.get('error')}")
            return None
        res = body["result"]
        if res.get("resultType") == "task":
            res = self._await_task(name, res["taskId"], token)
            if res is None:
                return None
        return self._judge(name, res, check)

    def _await_task(self, name: str, task_id: str, token: str) -> dict[str, Any] | None:
        deadline = time.time() + 600
        while time.time() < deadline:
            _, body = self.post("tasks/get", {"taskId": task_id}, token=token, tasks=True)
            task = body.get("result") or {}
            if task.get("status") == "completed":
                return task["result"]
            if task.get("status") in ("failed", "cancelled"):
                self.record(name, "FAIL", f"task {task.get('status')}: {task.get('error') or task.get('statusMessage')}")
                return None
            time.sleep(min(2.0, (task.get("pollIntervalMs") or 1000) / 1000))
        self.record(name, "FAIL", "task did not finish in 10 minutes")
        return None

    def _judge(self, name: str, res: dict[str, Any], check) -> dict[str, Any] | None:
        sc = res.get("structuredContent")
        texts = " ".join(c.get("text", "") for c in res.get("content") or [])
        if "verityngn analyze" in texts or "rfkit review" in texts:
            self.record(name, "FAIL", "returned a CLI command string instead of a result")
            return None
        if res.get("isError"):
            code = (sc or {}).get("code", "")
            status = "BLOCKED" if code in BLOCKING_CODES else "FAIL"
            self.record(name, status, f"{code}: {(sc or {}).get('message', '')}")
            return None
        if isinstance(sc, dict) and sc.get("status") == "running":
            self.record(name, "FAIL", "returned a pending handle where a final result was expected")
            return None
        problems = output_errors(name, sc)
        if problems:
            self.record(name, "FAIL", f"outputSchema violation: {problems[0]}")
            return None
        note = "validated against outputSchema"
        if check:
            try:
                note = check(sc) or note
            except AssertionError as exc:
                self.record(name, "FAIL", f"assertion: {exc}")
                return None
        self.record(name, "REAL", note)
        return sc


def run(live: bool) -> int:
    app = McpServer(ServerConfig(dev_mode=True, resource_url="http://127.0.0.1:0/mcp"))
    server, _ = serve_in_thread(app, "127.0.0.1", 0)
    host, port = server.server_address
    app.config.resource_url = f"http://{host}:{port}/mcp"
    gate = Gate(f"http://{host}:{port}")
    try:
        status, body = gate.post("server/discover", token=None)
        ok = status == 200 and body["result"]["supportedVersions"] == [VERSION]
        gate.record("server/discover", "REAL" if ok else "FAIL", f"HTTP {status}")
        status, body = gate.post("tools/list")
        n = len(body.get("result", {}).get("tools", []))
        gate.record("tools/list", "REAL" if n == 17 else "FAIL", f"{n} tools")

        doc = gate.tool(
            "register_document",
            {"text": FIXTURE, "media_type": "text/plain", "rights": "public_source"},
            check=lambda sc: (_assert(sc["outline"][0]["item"] == "1A", "Item 1A in outline"), f"{sc['doc_id']}, Items {[o['item'] for o in sc['outline']]}")[1],
        )
        if doc:
            gate.tool(
                "verify_quote",
                {"quote": "We may experience cybersecurity incidents", "source": doc["doc_id"]},
                check=lambda sc: (_assert(sc["match_mode"] == "exact", "exact match"), _assert(sc["target"]["anchor_status"] == "exact", "anchored"), "exact, anchored")[2],
            )
            gate.tool("assess_selection", {"target": {"source": doc["doc_id"], "scope": "document"}, "domain_pack": "securities_disclosure"},
                      check=lambda sc: f"{len(sc['records'])} records")
        gate.tool("analyze_video", {"video_id": "dQw4w9WgXcQ", "domain_pack": "securities_disclosure"})
        gate.tool("sanctions_match", {"name": "Example Person", "schema": "Person"})
        gate.tool("search_litigation", {"entity_id": "sr:ent:cik0000789019", "window": {"from": "2026-01-01", "to": "2026-02-01"}},
                  token="dev:gate:analyst:x:lic=courtlistener_commercial")
        status, body = gate.post("tools/call", {"name": "search_litigation", "arguments": {"entity_id": "sr:ent:cik0000789019", "window": {"from": "2026-01-01", "to": "2026-02-01"}}})
        lock = (body.get("result", {}).get("structuredContent") or {}).get("code")
        gate.record("lock: litigation without licence", "REAL" if lock == "LOCK_NO_LICENCE" else "FAIL", str(lock))
        status, body = gate.post("tools/call", {"name": "filings_search", "arguments": {"cik": "789019", "forms": ["8-K"], "window": {"from": "2024-01-01", "to": "2025-06-01"}}})
        lock = (body.get("result", {}).get("structuredContent") or {}).get("code")
        gate.record("lock: window over 366 days", "REAL" if lock == "LOCK_WINDOW" else "FAIL", str(lock))

        if live:
            gate.tool("resolve_entity", {"ticker": "MSFT"}, check=lambda sc: (_assert(sc["candidates"][0]["cik"] == "789019", "MSFT CIK"), "MSFT -> CIK 789019")[1])
            gate.tool("filings_search", {"cik": "789019", "forms": ["8-K"], "items": ["1.05"], "window": {"from": "2024-01-01", "to": "2024-03-31"}},
                      check=lambda sc: (_assert(any(f["accession"] == "0001193125-24-011295" for f in sc["filings"]), "Item 1.05 8-K found"), "Item 1.05 8-K of 2024-01-19 found")[1])
            gate.tool("get_filing_section", {"accession": "0001193125-24-011295", "cik": "789019", "item": "8-K:1.05"},
                      check=lambda sc: f"section target {sc['target']['section']['item']} in {sc['doc_id']}")
            gate.tool("get_filing_section", {"accession": "0001628280-26-067168", "item": "risk-factors"},
                      check=lambda sc: (_assert("/data/2130357/" in sc["url"], "issuer CIK, not the filing agent"),
                                        f"Anthropic S-1 {sc['target']['section']['item']} in {sc['doc_id']}")[1])
    finally:
        server.shutdown()

    from verityngn.agent.mcp_server import handle

    stdio = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "analyze_video", "arguments": {"url": "https://youtu.be/x"}}})
    text = stdio["result"]["content"][0]["text"]
    gate.record("stdio 3.1 analyze_video", "SURFACE", f"returns a command string, not a result: {text!r}")

    width = max(len(r[0]) for r in gate.rows)
    for name, status, detail in gate.rows:
        print(f"{name:<{width}}  {status:<8}  {detail}")
    counts = {s: sum(1 for r in gate.rows if r[1] == s) for s in ("REAL", "BLOCKED", "FAIL", "SURFACE")}
    print(f"\nREAL {counts['REAL']} · BLOCKED {counts['BLOCKED']} · FAIL {counts['FAIL']} · SURFACE {counts['SURFACE']}")
    return 1 if counts["FAIL"] else 0


def _assert(cond: bool, what: str) -> bool:
    if not cond:
        raise AssertionError(what)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--live", action="store_true", help="include SEC EDGAR round trips")
    sys.exit(run(parser.parse_args().live))
