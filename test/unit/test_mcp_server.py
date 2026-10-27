from verityngn.agent.mcp_server import handle


def test_tools_list_and_analyze():
    listed = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = {t["name"] for t in listed["result"]["tools"]}
    assert names == {"analyze_video", "review_disclosure", "get_report"}
    called = handle(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "analyze_video", "arguments": {"url": "https://youtu.be/x", "tier": "light"}},
        }
    )
    text = called["result"]["content"][0]["text"]
    assert "verityngn analyze --tier light" in text


def test_review_disclosure():
    called = handle(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "review_disclosure", "arguments": {"ticker": "MSFT", "csuite": True}},
        }
    )
    text = called["result"]["content"][0]["text"]
    assert "rfkit review --ticker MSFT" in text
    assert "--csuite" in text
