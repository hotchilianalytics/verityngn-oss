"""Server configuration from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Iterable


def _csv(value: str) -> tuple[str, ...]:
    return tuple(v.strip() for v in value.split(",") if v.strip())


@dataclass
class ServerConfig:
    resource_url: str = "http://127.0.0.1:8765/mcp"
    authorization_servers: tuple[str, ...] = ()
    allowed_origins: tuple[str, ...] = ()
    dev_mode: bool = False
    judgment_workspaces: tuple[str, ...] = ()
    documentation_url: str = "https://github.com/hotchilianalytics/verityngn-oss/blob/main/docs/agent/MCP_V2.md"
    video_poll_ms: int = 10_000
    document_poll_ms: int = 5_000
    large_section_chars: int = 90_000
    audit_path: str = ""
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def mcp_path(self) -> str:
        from urllib.parse import urlparse

        return urlparse(self.resource_url).path or "/mcp"

    @property
    def resource_metadata_url(self) -> str:
        from urllib.parse import urlparse

        u = urlparse(self.resource_url)
        return f"{u.scheme}://{u.netloc}/.well-known/oauth-protected-resource{u.path}"

    def judgment_enabled(self, tenant: str, workspace_ids: Iterable[str]) -> bool:
        on = set(self.judgment_workspaces)
        return tenant in on or bool(on & set(workspace_ids))

    @classmethod
    def from_env(cls) -> "ServerConfig":
        env = os.environ
        return cls(
            resource_url=env.get("SPLITRISK_RESOURCE_URL", cls.resource_url),
            authorization_servers=_csv(env.get("SPLITRISK_AUTH_ISSUER", "")),
            allowed_origins=_csv(env.get("SPLITRISK_ALLOWED_ORIGINS", "")),
            dev_mode=env.get("VERITYNGN_MCP_DEV_MODE", "").lower() in ("1", "true", "yes"),
            judgment_workspaces=_csv(env.get("SPLITRISK_JUDGMENT_WORKSPACES", "")),
            audit_path=env.get("SPLITRISK_AUDIT_LOG", ""),
        )
