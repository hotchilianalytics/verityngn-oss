"""Tool errors and JSON-RPC error codes for verityngn-mcp v2."""

from __future__ import annotations

from typing import Any, Optional

# JSON-RPC / MCP 2026-07-28 protocol codes.
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
HEADER_MISMATCH = -32020
MISSING_REQUIRED_CLIENT_CAPABILITY = -32021
UNSUPPORTED_PROTOCOL_VERSION = -32022
# Implementation-defined range (-32000..-32019).
UNAUTHORIZED = -32001
FORBIDDEN = -32003


class ToolFailure(Exception):
    """A tool execution error: returned as ``isError: true`` with a ``ToolError``."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        alternative: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.alternative = alternative
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.alternative:
            out["alternative"] = self.alternative
        if self.details:
            out["details"] = self.details
        return out


class EngineNotInstalled(ToolFailure):
    def __init__(self, engine: str, message: str, *, alternative: Optional[str] = None) -> None:
        super().__init__(
            "ENGINE_NOT_INSTALLED",
            message,
            alternative=alternative,
            details={"engine": engine},
        )


class NotFound(ToolFailure):
    """Missing handle, or a handle that belongs to another tenant (indistinguishable)."""

    def __init__(self, handle: str = "") -> None:
        super().__init__("NOT_FOUND", f"Not found: {handle}" if handle else "Not found")


class RpcError(Exception):
    """A JSON-RPC protocol error, optionally with a specific HTTP status."""

    def __init__(
        self,
        code: int,
        message: str,
        *,
        data: Optional[dict[str, Any]] = None,
        http_status: int = 200,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data
        self.http_status = http_status
        self.headers = headers or {}

    def to_dict(self) -> dict[str, Any]:
        err: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            err["data"] = self.data
        return err
