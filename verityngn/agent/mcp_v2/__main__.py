"""Run verityngn-mcp v2: ``python -m verityngn.agent.mcp_v2 [--host H] [--port P] [--dev]``.

Production configuration (environment):
  SPLITRISK_RESOURCE_URL   canonical MCP endpoint, e.g. https://mcp.example.com/mcp (token audience)
  SPLITRISK_AUTH_ISSUER    authorization server issuer (listed in RFC 9728 metadata)
  SPLITRISK_JWKS_URL       JWKS for access-token signatures
  SPLITRISK_ALLOWED_ORIGINS  comma-separated browser origins allowed to call the endpoint
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from verityngn.agent.mcp_v2.auth import JWTTokenValidator
from verityngn.agent.mcp_v2.config import ServerConfig
from verityngn.agent.mcp_v2.transport import make_http_server
from verityngn.agent.mcp_v2.server import McpServer


def build_server(dev: bool = False) -> McpServer:
    config = ServerConfig.from_env()
    if dev:
        config.dev_mode = True
    if config.dev_mode:
        return McpServer(config)
    issuer = config.authorization_servers[0] if config.authorization_servers else ""
    jwks = os.environ.get("SPLITRISK_JWKS_URL", "")
    if not issuer or not jwks:
        raise SystemExit("Set SPLITRISK_AUTH_ISSUER and SPLITRISK_JWKS_URL, or run with --dev on localhost.")
    validator = JWTTokenValidator(issuer=issuer, audience=config.resource_url, jwks_url=jwks)
    return McpServer(config, validator=validator)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m verityngn.agent.mcp_v2", description="verityngn-mcp v2 (Streamable HTTP)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--dev", action="store_true", help="accept dev:<tenant>:<role> tokens (loopback only)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s %(message)s", stream=sys.stderr)
    if args.dev and "SPLITRISK_RESOURCE_URL" not in os.environ:
        os.environ["SPLITRISK_RESOURCE_URL"] = f"http://{args.host}:{args.port}/mcp"
    app = build_server(dev=args.dev)
    server = make_http_server(app, args.host, args.port)
    logging.getLogger("verityngn.mcp_v2").info("Serving %s (dev=%s)", app.config.resource_url, app.config.dev_mode)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
