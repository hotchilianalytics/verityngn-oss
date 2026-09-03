"""Compare full vs direct ablation arm artefacts."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, Set


_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")
_STOP = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "have", "has", "had", "not", "but", "you", "your", "our", "their", "about",
    "into", "over", "under", "reference", "currently", "claim", "unverified",
    "video", "risk", "report",
}


def tokenize(text: str) -> Set[str]:
    toks = {t.lower() for t in _TOKEN_RE.findall(text or "")}
    return {t for t in toks if t not in _STOP and len(t) > 2}


def jaccard_overlap(a: str, b: str) -> float:
    sa, sb = tokenize(a), tokenize(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _count_citations(text: str) -> int:
    return len(re.findall(r"\[Reference:", text or "", flags=re.I))


def _count_urls(text: str) -> int:
    return len(re.findall(r"https?://\S+", text or ""))


def _count_headings(text: str) -> int:
    return len(re.findall(r"(?m)^#{1,3}\s+", text or ""))


def _read(path: str | None) -> str:
    if not path:
        return ""
    p = Path(path)
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8", errors="ignore")


def summarize_markdown(path: str | None) -> Dict[str, Any]:
    text = _read(path)
    return {
        "path": path,
        "chars": len(text),
        "bytes": len(text.encode("utf-8")),
        "citations": _count_citations(text),
        "urls": _count_urls(text),
        "headings": _count_headings(text),
        "top_tokens": Counter(tokenize(text)).most_common(15),
    }


def compare_arms(
    full_meta: Dict[str, Any] | None,
    direct_meta: Dict[str, Any] | None,
) -> Dict[str, Any]:
    full_md = (full_meta or {}).get("markdown_path")
    direct_md = (direct_meta or {}).get("markdown_path")
    full_sum = summarize_markdown(full_md)
    direct_sum = summarize_markdown(direct_md)
    overlap = jaccard_overlap(_read(full_md), _read(direct_md)) if full_md and direct_md else None

    return {
        "full": {
            "meta": {k: v for k, v in (full_meta or {}).items() if k != "raw"},
            "markdown": full_sum,
            "elapsed_sec": (full_meta or {}).get("elapsed_sec"),
        },
        "direct": {
            "meta": {k: v for k, v in (direct_meta or {}).items() if k != "raw"},
            "markdown": direct_sum,
            "elapsed_sec": (direct_meta or {}).get("elapsed_sec"),
        },
        "topic_jaccard": overlap,
        "decision_hint": (
            "direct_competitive"
            if overlap is not None and overlap >= 0.6
            else "keep_full_default"
            if overlap is not None
            else "insufficient_pair"
        ),
    }
