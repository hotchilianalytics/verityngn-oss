# VerityNgn agent surface (3.1.0)

Minimal MCP server and Agent Plugin package. Phase 1 of the platform refresh.

For the remote server that runs analyses and returns records (protocol 2026-07-28, Streamable HTTP, OAuth), see [verityngn-mcp v2](MCP_V2.md).

## Run the server

```bash
python -m verityngn.agent.mcp_server
```

Tools:

| Tool | What it does |
|------|----------------|
| `analyze_video` | Returns the `verityngn analyze` command for a URL or file |
| `review_disclosure` | Returns the `rfkit review` command for a ticker |
| `get_report` | Reads a local JSON report and returns top keys |

Plugin (Agent Plugins 1.0): [`plugins/verityngn/plugin.json`](../../plugins/verityngn/plugin.json) + [`plugins/verityngn/mcp.json`](../../plugins/verityngn/mcp.json). Skills live under `plugins/verityngn/skills/`.

This is a command-returning surface in 3.1.0: it does not run analyses from MCP, and its tests check command strings, not results. Hosted runs stay on verityindex.com; MCP execution is in v2.
