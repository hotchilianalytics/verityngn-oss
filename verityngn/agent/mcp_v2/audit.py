"""Per-call audit rows: the base of the general counsel's audit trail."""

from __future__ import annotations

import json
import logging
import threading
from typing import Any, Optional

from verityngn.agent.mcp_v2.records import canonical_hash, now_iso

logger = logging.getLogger("verityngn.mcp_v2.audit")


class AuditLog:
    def __init__(self, path: str = "") -> None:
        self.path = path
        self.rows: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def write(
        self,
        *,
        principal: Any,
        tool: str,
        arguments: dict[str, Any],
        record_ids: list[str],
        outcome: str,
        error_code: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        row: dict[str, Any] = {
            "at": now_iso(),
            "tenant": principal.tenant,
            "user": principal.sub,
            "role": principal.role,
            "tool": tool,
            "arguments_sha256": canonical_hash(arguments),
            "record_ids": record_ids,
            "outcome": outcome,
        }
        if error_code:
            row["error_code"] = error_code
        if extra:
            row.update(extra)
        with self._lock:
            self.rows.append(row)
            if self.path:
                with open(self.path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row, sort_keys=True) + "\n")
        logger.info("audit %s", json.dumps(row, sort_keys=True))
        return row
