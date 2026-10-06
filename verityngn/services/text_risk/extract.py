"""S15 disclosure-risk exposure.

Kim, Muhn & Nikolaev 2023 beat dictionary measures with an LLM. This module
ships a *labeled dictionary* baseline first (political / climate / AI) so the
text lane has a number on day one, plus an optional Gemini passthrough when
MULTISENSE credentials are live. Dictionary is the cold-start; LLM is the
upgrade. Neither is a tradable factor until event_time ICIR clears 0.40.
"""
from __future__ import annotations

import math
import re
from typing import Any, Optional

CATEGORIES: dict[str, tuple[str, ...]] = {
    "political": (
        "regulation", "tariff", "sanction", "congress", "election", "antitrust",
        "doj", "ftc", "geopolitical", "export control", "cfius",
    ),
    "climate": (
        "climate", "emissions", "carbon", "net zero", "esg", "sustainability",
        "drought", "wildfire", "transition risk", "scope 3",
    ),
    "ai": (
        "artificial intelligence", "generative ai", "gpu", "machine learning",
        "model risk", "hallucination", "foundation model", "llm",
    ),
}


def _hits(text: str, terms: tuple[str, ...]) -> int:
    blob = (text or "").lower()
    n = 0
    for t in terms:
        n += len(re.findall(re.escape(t), blob))
    return n


def score_disclosure_risk(
    text: str,
    *,
    source: str = "dictionary",
    doc_id: str = "",
    asof: Optional[str] = None,
    ticker: str = "",
) -> dict[str, Any]:
    tokens = re.findall(r"[A-Za-z']+", text or "")
    n = max(1, len(tokens))
    by_cat = {k: _hits(text, terms) / n for k, terms in CATEGORIES.items()}
    exposure = sum(by_cat.values())
    # squash to (0,1) without saturating small docs
    scaled = 1.0 - math.exp(-20.0 * exposure)
    return {
        "id": "S15_disclosure_risk_exposure",
        "doc_id": doc_id,
        "ticker": ticker,
        "asof": asof,
        "value": round(scaled, 6),
        "by_category": {k: round(v, 6) for k, v in by_cat.items()},
        "n_tokens": n,
        "source": source,
        "method": "keyword_intensity_exp_squash",
        "citation": "Kim, Muhn & Nikolaev, BFI WP 2023-132 / arXiv:2310.17721 (LLM upgrades this baseline)",
        "promote": "NO_PROMOTE",
    }
