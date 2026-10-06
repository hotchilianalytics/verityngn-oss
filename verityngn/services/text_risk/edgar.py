"""Minimal EDGAR 10-K/10-Q risk-section puller.

Hits the public data.sec.gov full-text archive. Respects a User-Agent.
Returns [] when offline / rate-limited — never fabricates filings.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any, Optional
from pathlib import Path

SEC_UA = os.environ.get("SEC_USER_AGENT", "VerityIndex research verityindex.com ajjc@verityindex.com")


def _get(url: str, timeout: int = 30) -> Optional[bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": SEC_UA, "Accept-Encoding": "identity"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:  # noqa: BLE001
        return None


def company_tickers(cache: Optional[Path] = None) -> dict[str, dict[str, Any]]:
    if cache and cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        return {str(v.get("ticker", "")).upper(): v for v in data.values() if isinstance(v, dict)}
    raw = _get("https://www.sec.gov/files/company_tickers.json")
    if not raw:
        return {}
    data = json.loads(raw.decode("utf-8", errors="replace"))
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(raw)
    return {str(v.get("ticker", "")).upper(): v for v in data.values() if isinstance(v, dict)}


_RISK_SPLIT = re.compile(r"item\s*1a[.\s]*risk\s*factors", re.I)
_NEXT_ITEM = re.compile(r"item\s*1b[.\s]|item\s*2[.\s]", re.I)


def extract_risk_section(html_or_text: str, limit: int = 80_000) -> str:
    text = re.sub(r"<[^>]+>", " ", html_or_text or " ")
    text = re.sub(r"\s+", " ", text)
    m = _RISK_SPLIT.search(text)
    if not m:
        return text[:limit]
    rest = text[m.end():]
    n = _NEXT_ITEM.search(rest)
    chunk = rest[: n.start()] if n else rest
    return chunk[:limit]


def qin_yang_loader(root: Path) -> list[dict[str, Any]]:
    """Walk a local Qin & Yang 2019-style audio+text dump (json/txt transcripts)."""
    rows = []
    if not root.exists():
        return rows
    for p in sorted(root.rglob("*")):
        if p.suffix.lower() not in {".txt", ".json"}:
            continue
        if p.suffix == ".json":
            try:
                obj = json.loads(p.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            text = obj.get("text") or obj.get("transcript") or ""
            ticker = str(obj.get("ticker") or "")
            date = obj.get("date") or obj.get("event_date")
        else:
            text = p.read_text(encoding="utf-8", errors="replace")
            ticker, date = "", None
        rows.append({"path": str(p), "text": text, "ticker": ticker, "event_date": date, "source": "qin_yang_local"})
    return rows
