"""Text disfluency and lightweight sentiment proxies (Tier-1 measured)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any


DISFLUENCY_PATTERNS = [
    r"\buh+\b",
    r"\bum+\b",
    r"\ber+\b",
    r"\bah+\b",
    r"\blike\b",
    r"\byou know\b",
    r"\bkind of\b",
    r"\bsort of\b",
    r"\bI mean\b",
]

POS_WORDS = {
    "great",
    "strong",
    "growth",
    "record",
    "excited",
    "confident",
    "opportunity",
    "accelerate",
    "outperform",
    "beat",
    "excellent",
    "innovation",
}
NEG_WORDS = {
    "challenging",
    "headwind",
    "uncertain",
    "decline",
    "weak",
    "risk",
    "pressure",
    "miss",
    "concern",
    "difficult",
    "slowdown",
    "caution",
}


@dataclass
class DisfluencyFeatures:
    count: int
    rate: float  # per token
    markers: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def extract_disfluency(text: str) -> DisfluencyFeatures:
    tokens = re.findall(r"[A-Za-z']+", text or "")
    n = max(1, len(tokens))
    markers: list[str] = []
    for pat in DISFLUENCY_PATTERNS:
        for m in re.finditer(pat, text or "", flags=re.IGNORECASE):
            markers.append(m.group(0).lower())
    return DisfluencyFeatures(count=len(markers), rate=len(markers) / n, markers=markers[:20])


def text_sentiment_proxy(text: str) -> float:
    """Crude lexicon polarity in [-1, 1]. Not a clinical emotion score."""
    tokens = [t.lower() for t in re.findall(r"[A-Za-z']+", text or "")]
    if not tokens:
        return 0.0
    pos = sum(1 for t in tokens if t in POS_WORDS)
    neg = sum(1 for t in tokens if t in NEG_WORDS)
    return float((pos - neg) / max(1, pos + neg)) if (pos + neg) else 0.0
