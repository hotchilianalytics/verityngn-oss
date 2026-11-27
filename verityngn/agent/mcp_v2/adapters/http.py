"""Minimal JSON-over-HTTP helper for upstream providers (patched in tests)."""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Optional

from verityngn.agent.mcp_v2.errors import ToolFailure


class RateLimiter:
    def __init__(self, per_second: float) -> None:
        self._interval = 1.0 / per_second
        self._lock = threading.Lock()
        self._next = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            delay = self._next - now
            self._next = max(now, self._next) + self._interval
        if delay > 0:
            time.sleep(delay)


def request(
    url: str,
    *,
    method: str = "GET",
    headers: Optional[dict[str, str]] = None,
    body: Optional[dict[str, Any]] = None,
    timeout: int = 30,
    provider: str = "upstream",
) -> bytes:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    hdrs = {"Accept": "application/json", "Accept-Encoding": "identity", **(headers or {})}
    if data is not None:
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed provider hosts
            return resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise ToolFailure("QUOTA", f"{provider} rate limit reached; try again shortly.") from None
        raise ToolFailure("UPSTREAM", f"{provider} returned HTTP {exc.code}.") from None
    except Exception as exc:  # noqa: BLE001
        raise ToolFailure("UPSTREAM", f"{provider} request failed: {type(exc).__name__}") from None


def request_json(url: str, **kwargs: Any) -> Any:
    raw = request(url, **kwargs)
    try:
        return json.loads(raw.decode("utf-8"))
    except ValueError:
        raise ToolFailure("UPSTREAM", f"{kwargs.get('provider', 'upstream')} returned invalid JSON.") from None
