"""OCR (on-screen text) and geographical / venue cues for the text modality."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional
import hashlib
import re


@dataclass
class OCRGeoResult:
    video_id: str
    on_screen_text: list[dict[str, Any]] = field(default_factory=list)
    venues: list[str] = field(default_factory=list)
    geo_hints: list[str] = field(default_factory=list)
    backend: str = "synthetic"
    gated: bool = False
    not_for_employment_use: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_VENUE_PATTERNS = [
    (r"\bGTC\b", "NVIDIA GTC"),
    (r"\bWWDC\b", "Apple WWDC"),
    (r"\bBuild\b", "Microsoft Build"),
    (r"\bDavos\b", "World Economic Forum Davos"),
    (r"\bCNBC\b", "CNBC"),
    (r"\bBloomberg\b", "Bloomberg"),
    (r"\bearnings\b", "Earnings call"),
]


def _seed_text(video_id: str) -> list[dict[str, Any]]:
    h = int(hashlib.sha256(video_id.encode()).hexdigest()[:4], 16)
    samples = [
        {"t_sec": 5.0, "text": "Q3 FY2025 Earnings", "kind": "chyron"},
        {"t_sec": 12.0, "text": "Revenue +12% YoY", "kind": "slide"},
        {"t_sec": 40.0, "text": "Forward-Looking Statements", "kind": "slide"},
    ]
    # Rotate which samples appear based on video_id
    return [samples[i % len(samples)] for i in range(1 + h % 3)]


def extract_ocr_geo(
    video_id: str,
    *,
    title: str = "",
    description: str = "",
    backend: Optional[str] = None,
) -> OCRGeoResult:
    used = backend or "synthetic"
    on_screen = _seed_text(video_id)
    blob = f"{title}\n{description}\n" + "\n".join(o["text"] for o in on_screen)
    venues = []
    for pat, name in _VENUE_PATTERNS:
        if re.search(pat, blob, flags=re.IGNORECASE):
            venues.append(name)
    geo = []
    for city in ("New York", "San Francisco", "Austin", "Singapore", "London"):
        if city.lower() in blob.lower():
            geo.append(city)
    return OCRGeoResult(
        video_id=video_id,
        on_screen_text=on_screen,
        venues=venues or ["unknown"],
        geo_hints=geo,
        backend=used,
    )
