"""Derive claim-anchored clip windows (timestamp ± margin) for multi-sense passes."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional
import re


def parse_timestamp(ts: Any) -> float:
    """Parse claim timestamps into seconds. Mirrors affect/extract._parse_timestamp."""
    if ts is None:
        return 0.0
    if isinstance(ts, (int, float)):
        return float(ts)
    s = str(ts).strip()
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)
    parts = s.split(":")
    try:
        parts_f = [float(p) for p in parts]
    except ValueError:
        return 0.0
    if len(parts_f) == 3:
        return parts_f[0] * 3600 + parts_f[1] * 60 + parts_f[2]
    if len(parts_f) == 2:
        return parts_f[0] * 60 + parts_f[1]
    return 0.0


@dataclass
class ClipWindow:
    claim_ids: list[Any] = field(default_factory=list)
    start_sec: float = 0.0
    end_sec: float = 0.0
    center_sec: float = 0.0
    high_stakes: bool = False
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def duration_sec(self) -> float:
        return max(0.0, self.end_sec - self.start_sec)


def _claim_stakes(claim: dict[str, Any]) -> tuple[bool, list[str]]:
    """Mark high-stakes / verdict-divergent claims for Tier B deep pass."""
    reasons: list[str] = []
    high = False
    verdict = ""
    vr = claim.get("verification_result")
    if isinstance(vr, dict):
        verdict = str(vr.get("result") or vr.get("verdict") or "").upper()
    elif isinstance(vr, str):
        verdict = vr.upper()
    if not verdict:
        pd = claim.get("probability_distribution") or {}
        if isinstance(pd, dict) and pd:
            verdict = max(pd.items(), key=lambda kv: float(kv[1] or 0.0))[0].upper()
    initial = str(claim.get("initial_assessment") or "").upper()
    if verdict in {"FALSE", "MIXED", "UNCERTAIN"}:
        high = True
        reasons.append(f"verdict:{verdict}")
    if initial and verdict and initial != verdict and verdict not in {"", "TRUE"}:
        high = True
        reasons.append("initial_vs_verified_diverge")
    text = (claim.get("claim_text") or "").lower()
    for kw in ("guidance", "revenue", "eps", "billion", "guarantee", "never", "always"):
        if kw in text:
            high = True
            reasons.append(f"keyword:{kw}")
            break
    return high, reasons


def build_clip_windows(
    claims: list[dict[str, Any]],
    *,
    margin_sec: float = 15.0,
    merge_gap_sec: float = 5.0,
    video_duration_sec: Optional[float] = None,
) -> list[ClipWindow]:
    """
    Build per-claim windows (ts ± margin_sec), merging overlaps / near-adjacent clips.

    Returns windows sorted by start_sec. Empty claims → empty list.
    """
    raw: list[ClipWindow] = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        t = parse_timestamp(claim.get("timestamp"))
        high, reasons = _claim_stakes(claim)
        start = max(0.0, t - margin_sec)
        end = t + margin_sec
        if video_duration_sec is not None:
            end = min(end, float(video_duration_sec))
        raw.append(
            ClipWindow(
                claim_ids=[claim.get("claim_id")],
                start_sec=start,
                end_sec=end,
                center_sec=t,
                high_stakes=high,
                reasons=list(reasons),
            )
        )
    if not raw:
        return []

    raw.sort(key=lambda w: w.start_sec)
    merged: list[ClipWindow] = [raw[0]]
    for w in raw[1:]:
        cur = merged[-1]
        if w.start_sec <= cur.end_sec + merge_gap_sec:
            cur.end_sec = max(cur.end_sec, w.end_sec)
            cur.claim_ids.extend(w.claim_ids)
            cur.high_stakes = cur.high_stakes or w.high_stakes
            cur.reasons = list(dict.fromkeys(cur.reasons + w.reasons))
            # recompute center as midpoint of span
            cur.center_sec = 0.5 * (cur.start_sec + cur.end_sec)
        else:
            merged.append(w)
    return merged


def tier_b_windows(windows: list[ClipWindow], *, max_clips: int = 12) -> list[ClipWindow]:
    """Select high-stakes windows for Tier B (cap cost)."""
    selected = [w for w in windows if w.high_stakes]
    if not selected:
        # Fall back to first few windows so harness always has something to score
        selected = list(windows[: min(3, len(windows))])
    return selected[:max_clips]
