"""verityngn-mcp v2: remote MCP server (protocol 2026-07-28) for SplitRisk.

The 3.1 stdio server in ``verityngn.agent.mcp_server`` stays for local and
coding-agent use.
"""

from verityngn.agent.mcp_v2.server import PROTOCOL_VERSION, SERVER_INFO, McpServer

__all__ = ["McpServer", "PROTOCOL_VERSION", "SERVER_INFO"]
