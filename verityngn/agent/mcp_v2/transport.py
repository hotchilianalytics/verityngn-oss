"""HTTP bindings: the standard library server (no extra dependencies) and ASGI."""

from __future__ import annotations

import ipaddress
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Awaitable, Callable

from verityngn.agent.mcp_v2.server import McpServer

MAX_BODY = 4 * 1024 * 1024 + 65536


def is_loopback(host: str) -> bool:
    if host in ("localhost", ""):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _handler(app: McpServer) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "verityngn-mcp/4.0.0"
        protocol_version = "HTTP/1.1"

        def _serve(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                self.send_response(413)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            body = self.rfile.read(length) if length else b""
            resp = app.handle_http(self.command, self.path, dict(self.headers.items()), body)
            self.send_response(resp.status)
            for k, v in resp.headers.items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(resp.body)))
            self.end_headers()
            if resp.body:
                self.wfile.write(resp.body)

        do_GET = do_POST = do_DELETE = do_PUT = do_PATCH = _serve

        def log_message(self, fmt: str, *args: Any) -> None:  # route to logging, not stderr spam
            import logging

            logging.getLogger("verityngn.mcp_v2.http").debug(fmt, *args)

    return Handler


def make_http_server(app: McpServer, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    if app.config.dev_mode and not is_loopback(host) and not _allow_remote_dev():
        raise RuntimeError("Dev mode tokens are refused on non-loopback binds. Set VERITYNGN_MCP_DEV_ALLOW_REMOTE=1 to override.")
    server = ThreadingHTTPServer((host, port), _handler(app))
    server.daemon_threads = True
    return server


def _allow_remote_dev() -> bool:
    import os

    return os.environ.get("VERITYNGN_MCP_DEV_ALLOW_REMOTE", "") == "1"


def serve_in_thread(app: McpServer, host: str = "127.0.0.1", port: int = 0) -> tuple[ThreadingHTTPServer, threading.Thread]:
    server = make_http_server(app, host, port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def asgi_app(app: McpServer) -> Callable[..., Awaitable[None]]:
    """ASGI 3 callable for uvicorn or Cloud Run. Dev-mode tokens are refused here unless explicitly allowed."""
    import asyncio

    if app.config.dev_mode and not _allow_remote_dev():
        raise RuntimeError("Dev mode is for loopback only; the ASGI app is for deployment. Set VERITYNGN_MCP_DEV_ALLOW_REMOTE=1 to override.")

    async def asgi(scope: dict[str, Any], receive: Callable[..., Awaitable[dict[str, Any]]], send: Callable[..., Awaitable[None]]) -> None:
        if scope["type"] == "lifespan":
            while True:
                event = await receive()
                if event["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif event["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        if scope["type"] != "http":
            return
        body = b""
        while True:
            event = await receive()
            body += event.get("body", b"")
            if len(body) > MAX_BODY:
                await send({"type": "http.response.start", "status": 413, "headers": []})
                await send({"type": "http.response.body", "body": b""})
                return
            if not event.get("more_body"):
                break
        headers = {k.decode("latin-1"): v.decode("latin-1") for k, v in scope.get("headers", [])}
        resp = await asyncio.to_thread(app.handle_http, scope["method"], scope["path"], headers, body)
        out_headers = [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in resp.headers.items()]
        await send({"type": "http.response.start", "status": resp.status, "headers": out_headers})
        await send({"type": "http.response.body", "body": resp.body})

    return asgi
