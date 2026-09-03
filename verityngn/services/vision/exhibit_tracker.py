"""Legal exhibit map from visual/modality claims — deposition and hearing sleeves."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from verityngn.services.report.display_labels import VISUAL_SOURCE_TYPES, is_visual_only_claim

_BATES_RE = re.compile(
    r"\b(?:EX(?:HIBIT)?\.?\s*)?(?:[A-Z]{1,3}[-\s]?)?\d{3,6}\b",
    re.IGNORECASE,
)


@dataclass
class ExhibitEntry:
    claim_id: Optional[int] = None
    timestamp: str = ""
    speaker: str = ""
    source_type: str = ""
    claim_text: str = ""
    ocr_snippet: str = ""
    bates_guess: str = ""
    bbox: Optional[dict[str, float]] = None
    on_screen_ms: Optional[int] = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExhibitMap:
    video_id: str
    schema_version: str = "0.1"
    n_exhibits: int = 0
    entries: list[ExhibitEntry] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["entries"] = [e.to_dict() if isinstance(e, ExhibitEntry) else e for e in self.entries]
        return d

    def write_json(self, path: Path | str) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        payload["n_exhibits"] = len(self.entries)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path


def _guess_bates(text: str) -> str:
    if not text:
        return ""
    m = _BATES_RE.search(text)
    return m.group(0).strip() if m else ""


def build_exhibit_map(
    video_id: str,
    claims: list[Any],
    *,
    include_spoken_with_ocr: bool = False,
) -> ExhibitMap:
    """
    Build exhibit tracker rows from claims with visual modalities.

    Pulls optional ocr_snippet, bbox, on_screen_ms from claim dict extras.
    """
    emap = ExhibitMap(video_id=video_id)
    for i, claim in enumerate(claims or []):
        if isinstance(claim, dict):
            st = str(claim.get("source_type") or "").lower()
            text = str(claim.get("claim_text") or "")
            ts = str(claim.get("timestamp") or "")
            speaker = str(claim.get("speaker") or "")
            cid = claim.get("claim_id", i)
            ocr = str(claim.get("ocr_snippet") or claim.get("on_screen_text") or "")
            bbox = claim.get("bbox") or claim.get("ocr_bbox")
            on_ms = claim.get("on_screen_ms")
        else:
            st = str(getattr(claim, "source_type", "") or "").lower()
            text = str(getattr(claim, "claim_text", "") or "")
            ts = str(getattr(claim, "timestamp", "") or "")
            speaker = str(getattr(claim, "speaker", "") or "")
            cid = getattr(claim, "claim_id", i)
            ocr = ""
            bbox = None
            on_ms = None

        visual = is_visual_only_claim(st) or st in VISUAL_SOURCE_TYPES
        if not visual and not (include_spoken_with_ocr and ocr):
            continue

        entry = ExhibitEntry(
            claim_id=int(cid) if cid is not None else i,
            timestamp=ts,
            speaker=speaker,
            source_type=st or "unknown",
            claim_text=text,
            ocr_snippet=ocr or text[:240],
            bates_guess=_guess_bates(text) or _guess_bates(ocr),
            bbox=bbox if isinstance(bbox, dict) else None,
            on_screen_ms=int(on_ms) if on_ms is not None else None,
        )
        emap.entries.append(entry)

    emap.n_exhibits = len(emap.entries)
    if not emap.entries:
        emap.notes = "No visual/exhibit claims detected"
    return emap


def persist_exhibit_map(
    video_id: str,
    claims: list[Any],
    out_dir: Path | str,
) -> Optional[Path]:
    """Write `{video_id}_exhibit_map.json` beside report outputs."""
    out = Path(out_dir)
    emap = build_exhibit_map(video_id, claims)
    if not emap.entries:
        return None
    path = out / f"{video_id}_exhibit_map.json"
    emap.write_json(path)
    return path
