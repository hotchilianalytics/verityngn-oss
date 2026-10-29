"""OAuth 2.1 resource-server side: RFC 9728 metadata and bearer validation.

The authorization server is out of scope here. Token validation is pluggable:
``JWTTokenValidator`` checks issuer, audience, expiry and scopes against a JWKS
(or a static key); ``DevTokenValidator`` accepts ``dev:<tenant>:<role>[:<sub>]``
tokens for local work and is refused on non-loopback binds unless overridden.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, Protocol

from verityngn.agent.mcp_v2.contracts import ALL_SCOPES, ROLE_DEFAULT_SCOPES, SCOPES

ROLES = ("analyst", "gc", "junior", "admin")
_TENANT = re.compile(r"^[a-z0-9-]{1,63}$")


@dataclass(frozen=True)
class Principal:
    sub: str
    tenant: str
    role: str
    scopes: frozenset[str]
    workspace_ids: tuple[str, ...] = ()
    licences: tuple[str, ...] = ()
    claims: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes

    @property
    def display_name(self) -> str:
        return str(self.claims.get("name") or self.claims.get("preferred_username") or self.sub)


class AuthError(Exception):
    """Raised by validators. ``error`` is the RFC 6750 error code."""

    def __init__(self, error: str, description: str, *, status: int = 401) -> None:
        super().__init__(description)
        self.error = error
        self.description = description
        self.status = status


class TokenValidator(Protocol):
    def validate(self, token: str) -> Principal: ...


def default_scopes(role: str) -> frozenset[str]:
    return frozenset(SCOPES[k] for k in ROLE_DEFAULT_SCOPES.get(role, []))


def principal_from_claims(
    claims: dict[str, Any],
    *,
    tenant_claim: str = "tenant_id",
    role_claim: str = "role",
) -> Principal:
    tenant = str(claims.get(tenant_claim) or "")
    role = str(claims.get(role_claim) or "")
    sub = str(claims.get("sub") or "")
    if not _TENANT.match(tenant):
        raise AuthError("invalid_token", f"token has no valid '{tenant_claim}' claim")
    if role not in ROLES:
        raise AuthError("invalid_token", f"token role must be one of {', '.join(ROLES)}")
    if not sub:
        raise AuthError("invalid_token", "token has no 'sub' claim")
    raw_scope = claims.get("scope", claims.get("scp", ""))
    scopes: Iterable[str] = raw_scope.split() if isinstance(raw_scope, str) else (raw_scope or [])
    return Principal(
        sub=sub,
        tenant=tenant,
        role=role,
        scopes=frozenset(s for s in scopes if s in ALL_SCOPES),
        workspace_ids=tuple(claims.get("workspace_ids") or ()),
        licences=tuple(claims.get("licences") or ()),
        claims=dict(claims),
    )


class JWTTokenValidator:
    """Validate signed JWT access tokens issued for this resource (RFC 8707 audience)."""

    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks_url: Optional[str] = None,
        key: Any = None,
        algorithms: Iterable[str] = ("RS256", "ES256"),
        leeway: int = 30,
        tenant_claim: str = "tenant_id",
        role_claim: str = "role",
    ) -> None:
        try:
            import jwt
        except ImportError as exc:
            raise RuntimeError("JWT validation needs PyJWT: pip install 'verityngn[mcp]'") from exc
        if not jwks_url and key is None:
            raise ValueError("JWTTokenValidator needs jwks_url or key")
        self.issuer = issuer
        self.audience = audience
        self.algorithms = list(algorithms)
        self.leeway = leeway
        self.tenant_claim = tenant_claim
        self.role_claim = role_claim
        self._key = key
        self._jwks = jwt.PyJWKClient(jwks_url, cache_keys=True) if jwks_url else None

    def validate(self, token: str) -> Principal:
        import jwt

        try:
            key = self._jwks.get_signing_key_from_jwt(token).key if self._jwks else self._key
            claims = jwt.decode(
                token,
                key=key,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer,
                leeway=self.leeway,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except jwt.ExpiredSignatureError:
            raise AuthError("invalid_token", "token expired") from None
        except jwt.InvalidAudienceError:
            raise AuthError("invalid_token", "token was not issued for this resource") from None
        except jwt.InvalidIssuerError:
            raise AuthError("invalid_token", "token issuer is not trusted") from None
        except jwt.PyJWTError as exc:
            raise AuthError("invalid_token", f"token rejected: {exc}") from None
        return principal_from_claims(claims, tenant_claim=self.tenant_claim, role_claim=self.role_claim)


class DevTokenValidator:
    """``dev:<tenant>:<role>[:<sub>][:lic=a,b][:name=First_Last]`` with the role's default scopes. Local use only."""

    def validate(self, token: str) -> Principal:
        parts = token.split(":")
        if len(parts) < 3 or parts[0] != "dev":
            raise AuthError("invalid_token", "dev mode expects tokens like dev:<tenant>:<role>[:<sub>]")
        tenant, role = parts[1], parts[2]
        sub = parts[3] if len(parts) > 3 and "=" not in parts[3] else f"dev-{role}"
        licences: list[str] = []
        name = ""
        for extra in parts[3:]:
            if extra.startswith("lic="):
                licences = [x for x in extra[4:].split(",") if x]
            elif extra.startswith("name="):
                name = extra[5:].replace("_", " ")
        claims = {
            "sub": sub,
            "tenant_id": tenant,
            "role": role,
            "scope": " ".join(sorted(default_scopes(role))),
            "licences": licences,
            "dev": True,
        }
        if name:
            claims["name"] = name
        return principal_from_claims(claims)


def protected_resource_metadata(
    *,
    resource: str,
    authorization_servers: list[str],
    resource_name: str = "VerityNgn MCP (SplitRisk)",
    documentation: Optional[str] = None,
) -> dict[str, Any]:
    """RFC 9728 document served at ``/.well-known/oauth-protected-resource``."""
    meta: dict[str, Any] = {
        "resource": resource,
        "authorization_servers": authorization_servers,
        "scopes_supported": ALL_SCOPES,
        "bearer_methods_supported": ["header"],
        "resource_name": resource_name,
    }
    if documentation:
        meta["resource_documentation"] = documentation
    return meta


def www_authenticate(
    *,
    resource_metadata_url: str,
    error: Optional[str] = None,
    description: Optional[str] = None,
    scopes: Optional[Iterable[str]] = None,
) -> str:
    parts = []
    if error:
        parts.append(f'error="{error}"')
    if scopes:
        parts.append(f'scope="{" ".join(scopes)}"')
    parts.append(f'resource_metadata="{resource_metadata_url}"')
    if description:
        safe = "".join(c if 0x20 <= ord(c) <= 0x7E and c not in '"\\' else "'" if c == '"' else " " for c in description)
        parts.append(f'error_description="{safe}"')
    return "Bearer " + ", ".join(parts)
