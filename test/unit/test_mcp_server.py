"""3.1 stdio server: a command surface, not execution.

``analyze_video`` and ``review_disclosure`` return CLI strings by design; the
tests below say so explicitly. Only ``get_report`` produces a real result, and
its test asserts that result. Hosted execution is covered by test/unit/mcp_v2
and scripts/ci/mcp_ship_gate.py.
"""

import json

from verityngn.agent.mcp_server import handle


def _call(name: str, arguments: dict) -> str:
    out = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": name, "arguments": arguments}})
    return out["result"]["content"][0]["text"]


def test_tools_list():
    listed = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = {t["name"] for t in listed["result"]["tools"]}
    assert names == {"analyze_video", "review_disclosure", "get_report"}


def test_analyze_video_is_a_command_surface_not_a_result():
    text = _call("analyze_video", {"url": "https://youtu.be/x", "tier": "light"})
    assert text == "verityngn analyze --tier light 'https://youtu.be/x'"
    assert "claims" not in text and "records" not in text


def test_review_disclosure_is_a_command_surface_not_a_result():
    text = _call("review_disclosure", {"ticker": "MSFT", "csuite": True})
    assert text.startswith("rfkit review --ticker MSFT") and "--csuite" in text


def test_get_report_reads_the_real_file(tmp_path):
    report = {"video_id": "tLJC8hkK-ao", "claims": [{"claim_text": "a"}], "overall": "UNRESOLVED"}
    path = tmp_path / "r_report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    out = json.loads(_call("get_report", {"path": str(path)}))
    assert out == {"path": str(path), "top_keys": ["video_id", "claims", "overall"], "bytes": path.stat().st_size}
    missing = json.loads(_call("get_report", {"path": str(tmp_path / "nope.json")}))
    assert missing["error"].startswith("not found")
