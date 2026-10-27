"""Minimal MCP server for VerityNgn 3.1 agent surface.

Tools: analyze_video, review_disclosure, get_report.
Stdio JSON-RPC. No crawl. No lie-detector language.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROTOCOL = "2024-11-05"

TOOLS = [
    {
        "name": "analyze_video",
        "description": "Return the CLI to run a VerityNgn claim-risk analysis on a YouTube URL or local file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "YouTube URL"},
                "file": {"type": "string", "description": "Local mp4 path"},
                "tier": {
                    "type": "string",
                    "enum": ["light", "full", "local-light", "local-full", "auto"],
                    "default": "auto",
                },
                "deep": {"type": "boolean", "default": False},
            },
        },
    },
    {
        "name": "review_disclosure",
        "description": "Return the CLI to run an rfkit disclosure review (Item 1A vs own record).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "committee": {"type": "boolean", "default": True},
                "csuite": {"type": "boolean", "default": False},
                "offline": {"type": "boolean", "default": True},
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_report",
        "description": "Read a local VerityNgn or rfkit JSON report from disk.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
]


def _result(id_, payload: dict) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": payload}


def _error(id_, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def _analyze(args: dict) -> str:
    tier = args.get("tier") or "auto"
    deep = " --deep" if args.get("deep") else ""
    if args.get("file"):
        return f"verityngn analyze --tier {tier} -f {args['file']}{deep}"
    url = args.get("url") or "<url>"
    return f"verityngn analyze --tier {tier} '{url}'{deep}"


def _review(args: dict) -> str:
    ticker = args["ticker"]
    cmd = f"rfkit review --ticker {ticker}"
    if args.get("committee", True):
        cmd += " --committee"
    if args.get("csuite"):
        cmd += " --csuite"
    if args.get("offline", True):
        cmd += " --offline --no-docket"
    return cmd


def _get_report(args: dict) -> str:
    path = Path(args["path"]).expanduser()
    if not path.is_file():
        return json.dumps({"error": f"not found: {path}"})
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        keys = list(data)[:12]
        return json.dumps({"path": str(path), "top_keys": keys, "bytes": path.stat().st_size})
    return json.dumps({"path": str(path), "type": type(data).__name__})


def handle(msg: dict) -> dict | None:
    mid = msg.get("id")
    method = msg.get("method")
    params = msg.get("params") or {}
    if method == "initialize":
        return _result(
            mid,
            {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "verityngn", "version": "3.1.0"},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return _result(mid, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if name == "analyze_video":
            text = _analyze(args)
        elif name == "review_disclosure":
            text = _review(args)
        elif name == "get_report":
            text = _get_report(args)
        else:
            return _error(mid, -32601, f"unknown tool {name}")
        return _result(mid, {"content": [{"type": "text", "text": text}]})
    if method == "ping":
        return _result(mid, {})
    return _error(mid, -32601, f"unknown method {method}")


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        reply = handle(msg)
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
