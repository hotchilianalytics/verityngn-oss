"""Streamable HTTP (2026-07-28) over a real socket, auth metadata and token validation."""

from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.request

import pytest

from verityngn.agent.mcp_v2.auth import AuthError, JWTTokenValidator
from verityngn.agent.mcp_v2.config import ServerConfig
from verityngn.agent.mcp_v2.server import McpServer
from verityngn.agent.mcp_v2.transport import asgi_app, make_http_server, serve_in_thread

from .conftest import VERSION, fake_adapters, make_server


@pytest.fixture
def live():
    app = make_server(allowed_origins=("https://app.splitrisk.example",))
    server, _ = serve_in_thread(app, "127.0.0.1", 0)
    host, port = server.server_address
    app.config.resource_url = f"http://{host}:{port}/mcp"
    yield f"http://{host}:{port}"
    server.shutdown()


def _post(base, method, params=None, *, token="dev:acme:analyst", headers=None, version=VERSION, body_version=VERSION, http_method="POST", path="/mcp", body=None):
    params = dict(params or {})
    params["_meta"] = {"io.modelcontextprotocol/protocolVersion": body_version, "io.modelcontextprotocol/clientCapabilities": {}}
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "Mcp-Method": method}
    if version:
        h["MCP-Protocol-Version"] = version
    if method == "tools/call":
        h["Mcp-Name"] = params.get("name", "")
    if token:
        h["Authorization"] = f"Bearer {token}"
    h.update(headers or {})
    data = body if body is not None else json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(base + path, data=data if http_method in ("POST", "PUT") else None, headers=h, method=http_method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            return resp.status, dict(resp.headers), json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, dict(exc.headers), json.loads(raw) if raw else None


def test_server_discover_without_auth(live):
    status, headers, body = _post(live, "server/discover", token=None)
    assert status == 200 and headers["Content-Type"] == "application/json"
    res = body["result"]
    assert res["resultType"] == "complete"
    assert res["supportedVersions"] == ["2026-07-28"]
    assert res["capabilities"]["extensions"]["io.modelcontextprotocol/tasks"] == {}
    assert res["capabilities"]["extensions"]["io.modelcontextprotocol/ui"] == {"mimeTypes": ["text/html;profile=mcp-app"]}
    assert res["_meta"]["io.modelcontextprotocol/serverInfo"]["version"] == "4.0.0"
    assert res["ttlMs"] > 0 and res["cacheScope"] == "public"
    assert "likelihood is never computed" in res["instructions"]


def test_tools_list_is_cacheable_and_real_tool_call_returns_structured_result(live):
    status, _, body = _post(live, "tools/list")
    assert status == 200
    res = body["result"]
    assert len(res["tools"]) == 17 and res["cacheScope"] == "public" and res["ttlMs"] > 0
    status, _, body = _post(live, "tools/call", {"name": "register_document", "arguments": {"text": "ITEM 1A. RISK FACTORS\nWe may lose data.", "media_type": "text/plain", "rights": "public_source"}})
    assert status == 200
    sc = body["result"]["structuredContent"]
    assert sc["doc_id"].startswith("sr:doc:acme/") and sc["outline"][0]["item"] == "1A"
    assert body["result"]["content"][0]["type"] == "text"


@pytest.mark.parametrize(
    "kwargs,code",
    [
        ({"version": None}, -32020),
        ({"body_version": "2025-11-25"}, -32020),
        ({"version": "1900-01-01", "body_version": "1900-01-01"}, -32022),
        ({"headers": {"Mcp-Method": "tools/call"}}, -32020),
    ],
)
def test_header_validation_errors(live, kwargs, code):
    status, _, body = _post(live, "tools/list", **kwargs)
    assert status == 400
    assert body["error"]["code"] == code
    if code == -32022:
        assert body["error"]["data"] == {"supported": ["2026-07-28"], "requested": "1900-01-01"}


def test_mcp_name_required_and_base64_sentinel_decoded(live):
    params = {"name": "get_record", "arguments": {"record_id": "sr:rec:acme/missing"}}
    status, _, body = _post(live, "tools/call", params, headers={"Mcp-Name": "get_report"})
    assert status == 400 and body["error"]["code"] == -32020
    status, _, body = _post(live, "tools/call", params, headers={"Mcp-Name": "=?base64?Z2V0X3JlY29yZA==?="})
    assert status == 200 and body["result"]["structuredContent"]["code"] == "NOT_FOUND"


def test_get_delete_and_unknown_methods(live):
    assert _post(live, "tools/list", http_method="GET")[0] == 405
    assert _post(live, "tools/list", http_method="DELETE")[0] == 405
    status, _, body = _post(live, "ping")
    assert status == 404 and body["error"]["code"] == -32601
    assert _post(live, "tools/list", path="/elsewhere")[0] == 404


def test_notifications_get_202(live):
    data = json.dumps({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {}}).encode()
    status, _, body = _post(live, "notifications/cancelled", body=data)
    assert status == 202 and body is None


def test_session_ids_are_ignored(live):
    status, headers, _ = _post(live, "tools/list", headers={"Mcp-Session-Id": "abc", "Last-Event-ID": "7"})
    assert status == 200 and "Mcp-Session-Id" not in headers


def test_origin_validation(live):
    assert _post(live, "tools/list", headers={"Origin": "https://evil.example"})[0] == 403
    assert _post(live, "tools/list", headers={"Origin": "https://app.splitrisk.example"})[0] == 200


def test_unauthenticated_and_bad_tokens_get_rfc9728_challenge(live):
    status, headers, body = _post(live, "tools/list", token=None)
    assert status == 401
    challenge = headers["WWW-Authenticate"]
    assert challenge.startswith("Bearer ") and f'resource_metadata="{live}/.well-known/oauth-protected-resource/mcp"' in challenge
    status, headers, _ = _post(live, "tools/list", token="not-a-dev-token")
    assert status == 401 and 'error="invalid_token"' in headers["WWW-Authenticate"]
    status, _, _ = _post(live, "tools/list", token="dev:Bad_Tenant:analyst")
    assert status == 401


def test_protected_resource_metadata_both_paths(live):
    for path in ("/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp"):
        with urllib.request.urlopen(live + path, timeout=10) as resp:
            meta = json.loads(resp.read())
        assert meta["resource"] == f"{live}/mcp"
        assert meta["authorization_servers"] == ["https://auth.example.com"]
        assert "splitrisk.review.decide" in meta["scopes_supported"]
        assert meta["bearer_methods_supported"] == ["header"]


def test_dev_mode_refuses_remote_bind(monkeypatch):
    monkeypatch.delenv("VERITYNGN_MCP_DEV_ALLOW_REMOTE", raising=False)
    with pytest.raises(RuntimeError):
        make_http_server(make_server(), "0.0.0.0", 0)
    with pytest.raises(ValueError):
        McpServer(ServerConfig(dev_mode=False), adapters=fake_adapters())


def test_asgi_binding_round_trip(monkeypatch):
    monkeypatch.delenv("VERITYNGN_MCP_DEV_ALLOW_REMOTE", raising=False)
    with pytest.raises(RuntimeError):
        asgi_app(make_server())
    monkeypatch.setenv("VERITYNGN_MCP_DEV_ALLOW_REMOTE", "1")
    app = asgi_app(make_server())
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": VERSION}}}).encode()
    scope = {"type": "http", "method": "POST", "path": "/mcp", "headers": [(b"mcp-protocol-version", VERSION.encode()), (b"mcp-method", b"server/discover")]}
    sent = []

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(msg):
        sent.append(msg)

    asyncio.run(app(scope, receive, send))
    assert sent[0]["status"] == 200
    assert json.loads(sent[1]["body"])["result"]["supportedVersions"] == ["2026-07-28"]


jwt = pytest.importorskip("jwt")
KEY = "test-secret-key-that-is-long-enough-for-hs256"


def _token(**overrides):
    claims = {
        "iss": "https://auth.example.com",
        "aud": "https://mcp.example.com/mcp",
        "sub": "user-1",
        "exp": int(time.time()) + 300,
        "tenant_id": "acme",
        "role": "gc",
        "scope": "splitrisk.read splitrisk.review.decide unknown.scope",
        "licences": ["courtlistener_commercial"],
    }
    claims.update(overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, KEY, algorithm="HS256")


def test_jwt_validator_checks_issuer_audience_expiry_and_claims():
    v = JWTTokenValidator(issuer="https://auth.example.com", audience="https://mcp.example.com/mcp", key=KEY, algorithms=["HS256"])
    p = v.validate(_token())
    assert (p.tenant, p.role, p.sub) == ("acme", "gc", "user-1")
    assert p.scopes == frozenset({"splitrisk.read", "splitrisk.review.decide"})
    assert p.licences == ("courtlistener_commercial",)
    for bad in (_token(aud="https://other.example.com/mcp"), _token(iss="https://evil.example.com"), _token(exp=int(time.time()) - 600), _token(tenant_id=None), _token(role="ceo")):
        with pytest.raises(AuthError) as e:
            v.validate(bad)
        assert e.value.error == "invalid_token"


def test_jwt_principal_scopes_drive_http_403():
    v = JWTTokenValidator(issuer="https://auth.example.com", audience="https://mcp.example.com/mcp", key=KEY, algorithms=["HS256"])
    app = McpServer(ServerConfig(resource_url="https://mcp.example.com/mcp"), validator=v, adapters=fake_adapters())
    params = {"name": "register_document", "arguments": {"text": "x", "media_type": "text/plain", "rights": "public_source"},
              "_meta": {"io.modelcontextprotocol/protocolVersion": VERSION}}
    h = {"MCP-Protocol-Version": VERSION, "Mcp-Method": "tools/call", "Mcp-Name": "register_document", "Authorization": f"Bearer {_token()}"}
    resp = app.handle_http("POST", "/mcp", h, json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params}).encode())
    assert resp.status == 403
    assert 'scope="splitrisk.assess"' in resp.headers["WWW-Authenticate"]
    assert 'resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource/mcp"' in resp.headers["WWW-Authenticate"]
