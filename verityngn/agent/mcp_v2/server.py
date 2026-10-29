"""verityngn-mcp v2: stateless MCP 2026-07-28 over Streamable HTTP.

``McpServer.handle_http`` is transport-agnostic (method, path, headers, body in;
status, headers, body out). ``transport.py`` binds it to the standard library HTTP
server and to ASGI.
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from verityngn.agent.mcp_v2 import ui
from verityngn.agent.mcp_v2.adapters import Adapters
from verityngn.agent.mcp_v2.audit import AuditLog
from verityngn.agent.mcp_v2.auth import (
    AuthError,
    DevTokenValidator,
    Principal,
    TokenValidator,
    default_scopes,
    protected_resource_metadata,
    www_authenticate,
)
from verityngn.agent.mcp_v2.config import ServerConfig
from verityngn.agent.mcp_v2.contracts import TOOL_NAMES, published_tools, required_scopes
from verityngn.agent.mcp_v2.errors import (
    FORBIDDEN,
    HEADER_MISMATCH,
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    MISSING_REQUIRED_CLIENT_CAPABILITY,
    PARSE_ERROR,
    UNAUTHORIZED,
    UNSUPPORTED_PROTOCOL_VERSION,
    NotFound,
    RpcError,
    ToolFailure,
)
from verityngn.agent.mcp_v2.documents import document_payload
from verityngn.agent.mcp_v2.records import view
from verityngn.agent.mcp_v2.schema_defs import SCHEMA_ID, definitions_document
from verityngn.agent.mcp_v2.store import MemoryStore
from verityngn.agent.mcp_v2.tasks import EXTENSION as TASKS_EXT
from verityngn.agent.mcp_v2.tasks import TaskManager
from verityngn.agent.mcp_v2.tools import CallContext, ToolRunner, output_errors

logger = logging.getLogger("verityngn.mcp_v2")

PROTOCOL_VERSION = "2026-07-28"
SUPPORTED_VERSIONS = [PROTOCOL_VERSION]
SERVER_INFO = {"name": "verityngn", "title": "VerityNgn MCP (SplitRisk)", "version": "4.0.0"}
UI_EXT = "io.modelcontextprotocol/ui"
META_VERSION = "io.modelcontextprotocol/protocolVersion"
META_CAPS = "io.modelcontextprotocol/clientCapabilities"
META_SERVER = "io.modelcontextprotocol/serverInfo"
NAMED_METHODS = {"tools/call": "name", "resources/read": "uri", "prompts/get": "name"}
LIST_TTL_MS = 300_000
INSTRUCTIONS = (
    "SplitRisk disclosure and delivery risk tools. Resolve an issuer with resolve_entity before any directed query. "
    "Every search needs a bounded window of at most 366 days that does not end in the future; nothing is scheduled "
    "or monitored. Results show coverage (who already holds a dated public quote) and a severity tag; likelihood is "
    "never computed. Verdicts are Supported, Contested or Unresolved. Not legal advice. When a call returns an error "
    "with an 'alternative', offer that alternative to the user."
)
NORMALIZER_URI = "splitrisk://normalizer/sr-norm-1"
NORMALIZER_VECTORS = Path(__file__).resolve().parent / "data" / "sr-norm-1.vectors.json"
_B64 = re.compile(r"^=\?base64\?(.*)\?=$")
_HEADER_SAFE = re.compile(r"^[\x20-\x7e]*$")


@dataclass
class HttpResponse:
    status: int
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""


def _json_response(status: int, payload: Any, headers: Optional[dict[str, str]] = None) -> HttpResponse:
    return HttpResponse(status, {"Content-Type": "application/json", **(headers or {})}, json.dumps(payload).encode("utf-8"))


def _decode_header(value: str) -> str:
    m = _B64.match(value)
    if not m:
        if not _HEADER_SAFE.match(value):
            raise RpcError(HEADER_MISMATCH, "Header value contains invalid characters", http_status=400)
        return value
    try:
        return base64.b64decode(m.group(1), validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        raise RpcError(HEADER_MISMATCH, "Header value is not valid base64", http_status=400) from None


class McpServer:
    def __init__(
        self,
        config: Optional[ServerConfig] = None,
        *,
        validator: Optional[TokenValidator] = None,
        store: Optional[MemoryStore] = None,
        adapters: Optional[Adapters] = None,
        tasks: Optional[TaskManager] = None,
    ) -> None:
        self.config = config or ServerConfig.from_env()
        if validator is None:
            if not self.config.dev_mode:
                raise ValueError("A token validator is required unless dev mode is on")
            validator = DevTokenValidator()
        self.validator = validator
        self.store = store or MemoryStore()
        self.audit = AuditLog(self.config.audit_path)
        self.tasks = tasks or TaskManager()
        self.runner = ToolRunner(
            store=self.store, adapters=adapters or Adapters(), tasks=self.tasks, config=self.config, audit=self.audit
        )
        self._tools = published_tools()

    # ------------------------------------------------------------------ HTTP

    def _prm(self) -> dict[str, Any]:
        return protected_resource_metadata(
            resource=self.config.resource_url,
            authorization_servers=list(self.config.authorization_servers),
            documentation=self.config.documentation_url,
        )

    def handle_http(self, method: str, path: str, headers: Mapping[str, str], body: bytes) -> HttpResponse:
        h = {k.lower(): v for k, v in headers.items()}
        path = path.split("?", 1)[0]
        if path.startswith("/.well-known/oauth-protected-resource"):
            if method != "GET":
                return HttpResponse(405, {"Allow": "GET"})
            return _json_response(200, self._prm(), {"Cache-Control": "public, max-age=3600"})
        if path == "/healthz":
            return _json_response(200, {"ok": True})
        if path != self.config.mcp_path:
            return HttpResponse(404)
        if method != "POST":
            return HttpResponse(405, {"Allow": "POST"})
        origin = h.get("origin")
        if origin and origin not in self.config.allowed_origins:
            return _json_response(403, {"jsonrpc": "2.0", "error": {"code": INVALID_REQUEST, "message": "Origin not allowed"}})
        try:
            msg = json.loads(body.decode("utf-8") or "null")
        except (UnicodeDecodeError, ValueError):
            return _json_response(400, {"jsonrpc": "2.0", "id": None, "error": {"code": PARSE_ERROR, "message": "Parse error"}})
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0" or not isinstance(msg.get("method"), str):
            return _json_response(400, {"jsonrpc": "2.0", "id": None, "error": {"code": INVALID_REQUEST, "message": "Expected one JSON-RPC request or notification"}})
        is_notification = "id" not in msg
        mid = msg.get("id")
        try:
            self._validate_headers(msg, h, notification=is_notification)
            if is_notification:
                return HttpResponse(202)
            principal = self._authenticate(msg["method"], h)
            result = self.dispatch(msg, principal)
            return _json_response(200, {"jsonrpc": "2.0", "id": mid, "result": result})
        except RpcError as exc:
            return _json_response(exc.http_status, {"jsonrpc": "2.0", "id": mid, "error": exc.to_dict()}, exc.headers)
        except Exception:  # noqa: BLE001
            logger.exception("Unhandled error in %s", msg.get("method"))
            return _json_response(500, {"jsonrpc": "2.0", "id": mid, "error": {"code": INTERNAL_ERROR, "message": "Internal error"}})

    def _validate_headers(self, msg: dict[str, Any], h: Mapping[str, str], *, notification: bool) -> None:
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        body_version = (params.get("_meta") or {}).get(META_VERSION)
        header_version = h.get("mcp-protocol-version")
        if notification:
            return
        if not header_version:
            raise RpcError(HEADER_MISMATCH, "Missing MCP-Protocol-Version header", http_status=400)
        if header_version != body_version:
            raise RpcError(
                HEADER_MISMATCH,
                f"Header mismatch: MCP-Protocol-Version '{header_version}' does not match body _meta value '{body_version}'",
                http_status=400,
            )
        if header_version not in SUPPORTED_VERSIONS:
            raise RpcError(
                UNSUPPORTED_PROTOCOL_VERSION,
                "Unsupported protocol version",
                data={"supported": SUPPORTED_VERSIONS, "requested": header_version},
                http_status=400,
            )
        header_method = h.get("mcp-method")
        if header_method is None:
            raise RpcError(HEADER_MISMATCH, "Missing Mcp-Method header", http_status=400)
        if header_method != msg["method"]:
            raise RpcError(HEADER_MISMATCH, f"Header mismatch: Mcp-Method '{header_method}' does not match body method '{msg['method']}'", http_status=400)
        field_name = NAMED_METHODS.get(msg["method"])
        if field_name:
            raw = h.get("mcp-name")
            if raw is None:
                raise RpcError(HEADER_MISMATCH, "Missing Mcp-Name header", http_status=400)
            value = _decode_header(raw)
            if value != params.get(field_name):
                raise RpcError(HEADER_MISMATCH, f"Header mismatch: Mcp-Name '{value}' does not match body value '{params.get(field_name)}'", http_status=400)

    def _challenge(self, status: int, code: int, message: str, *, error: Optional[str] = None, scopes: Optional[list[str]] = None, data: Optional[dict[str, Any]] = None) -> RpcError:
        header = www_authenticate(
            resource_metadata_url=self.config.resource_metadata_url, error=error, description=message, scopes=scopes
        )
        return RpcError(code, message, http_status=status, headers={"WWW-Authenticate": header}, data=data)

    def _authenticate(self, method: str, h: Mapping[str, str]) -> Optional[Principal]:
        if method == "server/discover":
            return None
        auth = h.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            raise self._challenge(401, UNAUTHORIZED, "Bearer token required", scopes=["splitrisk.read", "splitrisk.assess", "splitrisk.search", "splitrisk.export"])
        try:
            return self.validator.validate(auth[7:].strip())
        except AuthError as exc:
            raise self._challenge(exc.status, UNAUTHORIZED, exc.description, error=exc.error) from None

    # -------------------------------------------------------------- dispatch

    def _result(self, payload: dict[str, Any], *, cacheable: bool = False, scope: str = "public", ttl: int = LIST_TTL_MS) -> dict[str, Any]:
        out = {"resultType": "complete", **payload} if "resultType" not in payload else dict(payload)
        if cacheable:
            out["ttlMs"] = ttl
            out["cacheScope"] = scope
        meta = dict(out.get("_meta") or {})
        meta[META_SERVER] = SERVER_INFO
        out["_meta"] = meta
        return out

    @staticmethod
    def _client_has(params: dict[str, Any], extension: str) -> bool:
        caps = (params.get("_meta") or {}).get(META_CAPS) or {}
        return extension in (caps.get("extensions") or {})

    def dispatch(self, msg: dict[str, Any], principal: Optional[Principal]) -> dict[str, Any]:
        method = msg["method"]
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        if method == "server/discover":
            return self._result(
                {
                    "supportedVersions": SUPPORTED_VERSIONS,
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "extensions": {TASKS_EXT: {}, UI_EXT: {"mimeTypes": [ui.UI_MIME]}},
                    },
                    "instructions": INSTRUCTIONS,
                },
                cacheable=True,
                ttl=3_600_000,
            )
        assert principal is not None
        if method == "tools/list":
            return self._result({"tools": self._tools}, cacheable=True)
        if method == "tools/call":
            return self._tools_call(params, principal)
        if method == "resources/list":
            listing = [ui.resource_listing(n) for n in ui.WIDGET_NAMES]
            listing.append({"uri": "splitrisk://schema/v1", "name": "splitrisk_schema_v1", "title": "SplitRisk shared definitions", "mimeType": "application/schema+json"})
            listing.append({"uri": NORMALIZER_URI, "name": "sr_norm_1", "title": "sr-norm-1 definition and test vectors", "mimeType": "application/json"})
            return self._result({"resources": listing}, cacheable=True)
        if method == "resources/templates/list":
            templates = [
                {"uriTemplate": "splitrisk://documents/{doc_id}", "name": "document", "title": "Normalized text, outline and offset tables", "mimeType": "application/json"},
                {"uriTemplate": "splitrisk://records/{record_id}", "name": "record", "mimeType": "application/json"},
                {"uriTemplate": "splitrisk://reports/{report_id}", "name": "report", "mimeType": "application/json"},
                {"uriTemplate": "splitrisk://exports/{export_id}", "name": "export"},
            ]
            return self._result({"resourceTemplates": templates}, cacheable=True)
        if method == "resources/read":
            return self._resources_read(str(params.get("uri", "")), principal)
        if method in ("tasks/get", "tasks/update", "tasks/cancel"):
            if not self._client_has(params, TASKS_EXT):
                raise RpcError(
                    MISSING_REQUIRED_CLIENT_CAPABILITY,
                    "Missing required client capability",
                    data={"requiredCapabilities": {"extensions": {TASKS_EXT: {}}}},
                )
            task_id = str(params.get("taskId", ""))
            if method == "tasks/get":
                return self._result(self.tasks.get(task_id, principal.tenant))
            if method == "tasks/update":
                self.tasks.update(task_id, principal.tenant, params.get("inputResponses") or {})
                return self._result({})
            self.tasks.cancel(task_id, principal.tenant)
            return self._result({})
        raise RpcError(METHOD_NOT_FOUND, f"Method not found: {method}", http_status=404)

    def _tools_call(self, params: dict[str, Any], principal: Principal) -> dict[str, Any]:
        name = params.get("name")
        if name not in TOOL_NAMES:
            raise RpcError(INVALID_PARAMS, f"Unknown tool: {name}")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            raise RpcError(INVALID_PARAMS, "arguments must be an object")
        needed = required_scopes(name)
        if name == "record_review_action" and principal.role == "gc" and arguments.get("action") not in (None, "propose"):
            needed = ["splitrisk.review.decide"]
        if not any(principal.has_scope(s) for s in needed):
            raise self._scope_denied(name, needed, principal)
        ctx = CallContext(principal=principal, tasks_ok=self._client_has(params, TASKS_EXT))
        result = self.runner.call(name, arguments, ctx)
        if result.get("resultType") == "complete" and not result.get("isError"):
            problems = output_errors(name, result.get("structuredContent"))
            if problems:
                logger.error("Output of %s violates its outputSchema: %s", name, problems[:3])
                raise RpcError(INTERNAL_ERROR, f"{name} produced output that does not match its outputSchema")
        return self._result(result)

    def _scope_denied(self, name: str, needed: list[str], principal: Principal) -> RpcError:
        """403 ``insufficient_scope`` that keeps the allowed alternative visible.

        The alternative is repeated in the JSON-RPC message, in ``error.data``
        and in the challenge's ``error_description``, because clients differ in
        which of the three they surface. ``step_up`` is false when the caller's
        role never holds the scope, so re-authorizing cannot help.
        """
        reachable = [s for s in needed if s in default_scopes(principal.role)]
        step_up = bool(reachable)
        scope = reachable[0] if reachable else needed[0]
        if step_up:
            alternative = f"Re-authorize with scope {scope}."
        elif name == "analyze_video":
            alternative = "Ask an analyst or general counsel to run analyze_video, or assess a transcript you upload with register_document."
        elif name == "record_review_action":
            alternative = "Call record_review_action with action 'propose'; general counsel decides."
        else:
            alternative = "Ask an admin for access."
        message = f"{name} needs scope {' or '.join(needed)}. Instead: {alternative}"
        return self._challenge(
            403,
            FORBIDDEN,
            message,
            error="insufficient_scope",
            scopes=[scope],
            data={
                **({} if step_up else {"code": "LOCK_ROLE"}),
                "required_scopes": needed,
                "role": principal.role,
                "step_up": step_up,
                "alternative": alternative,
            },
        )

    def _resources_read(self, uri: str, principal: Principal) -> dict[str, Any]:
        if uri.startswith("ui://splitrisk/"):
            name = uri.rsplit("/", 1)[-1]
            if name not in ui.WIDGET_NAMES:
                raise RpcError(INVALID_PARAMS, "Resource not found", data={"uri": uri})
            return self._result({"contents": [ui.read(name)]}, cacheable=True)
        if uri == "splitrisk://schema/v1":
            doc = definitions_document()
            return self._result(
                {"contents": [{"uri": uri, "mimeType": "application/schema+json", "text": json.dumps(doc), "_meta": {"$id": SCHEMA_ID}}]},
                cacheable=True,
            )
        if uri == NORMALIZER_URI:
            return self._result(
                {"contents": [{"uri": uri, "mimeType": "application/json", "text": NORMALIZER_VECTORS.read_text(encoding="utf-8")}]},
                cacheable=True,
                ttl=86_400_000,
            )
        try:
            if uri.startswith("splitrisk://documents/"):
                doc = self.store.get_document(uri[len("splitrisk://documents/"):], principal.tenant)
                contents = [{"uri": uri, "mimeType": "application/json", "text": json.dumps(document_payload(doc))}]
                return self._result({"contents": contents}, cacheable=True, scope="private", ttl=86_400_000)
            if uri.startswith("splitrisk://records/"):
                rec = self.store.get_record(uri[len("splitrisk://records/"):], principal.tenant)
                text = json.dumps(view(rec, principal.role))
                contents = [{"uri": uri, "mimeType": "application/json", "text": text}]
            elif uri.startswith("splitrisk://reports/"):
                res = self.runner.get_report({"report_id": uri[len("splitrisk://reports/"):]}, CallContext(principal, False))
                contents = [{"uri": uri, "mimeType": "application/json", "text": json.dumps(res["structuredContent"])}]
            elif uri.startswith("splitrisk://exports/"):
                exp = self.store.get_export(uri[len("splitrisk://exports/"):], principal.tenant)
                if exp.media_type.startswith(("text/", "application/json", "application/ld+json")):
                    contents = [{"uri": uri, "mimeType": exp.media_type, "text": exp.data.decode("utf-8")}]
                else:
                    contents = [{"uri": uri, "mimeType": exp.media_type, "blob": base64.b64encode(exp.data).decode("ascii")}]
            else:
                raise NotFound(uri)
        except (NotFound, ToolFailure):
            raise RpcError(INVALID_PARAMS, "Resource not found", data={"uri": uri}) from None
        return self._result({"contents": contents}, cacheable=True, scope="private", ttl=0)
