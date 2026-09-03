"""Agency sponsor-readiness scores — visual-only and disclosure cues from claims."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from verityngn.services.report.display_labels import is_visual_only_claim

_DISCLOSURE_RE = re.compile(
    r"#\s*ad|paid\s+partnership|sponsored|affiliate\s+link|commission",
    re.IGNORECASE,
)
_CREDENTIAL_RE = re.compile(
    r"\b(dr\.?|md|ph\.?d|prof\.?|harvard|johns?\s*hopkins|stanford|mayo)\b",
    re.IGNORECASE,
)
_HIGH_RISK_VERDICTS = frozenset(
    {
        "LIKELY_FALSE",
        "HIGHLY_LIKELY_FALSE",
        "LIKELY TO BE FALSE",
        "HIGHLY LIKELY TO BE FALSE",
        "FALSE",
    }
)


@dataclass
class CredentialFlashEvent:
    timestamp: str
    claim_text: str
    source_type: str = "visual_text"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BrandSafetyScores:
    video_id: str
    scored_at: str = ""
    sku: str = "sponsor_readiness"
    overall_risk: str = "low"
    visual_only_high_risk_count: int = 0
    visual_only_claim_count: int = 0
    disclosure_on_screen_ms: int = 0
    credential_flash_events: list[CredentialFlashEvent] = field(default_factory=list)
    claim_risk_buckets: dict[str, int] = field(default_factory=lambda: {"high": 0, "medium": 0, "low": 0})
    press_release_flags: int = 0
    ci_hit_rate: float = 0.0
    sponsor_read_detected: bool = False
    undisclosed_affiliate_risk: str = "normal"
    recommended_action: str = "approve"
    top_flags: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["credential_flash_events"] = [
            e.to_dict() if isinstance(e, CredentialFlashEvent) else e
            for e in self.credential_flash_events
        ]
        return d

    def write_json(self, path: Path | str) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path


def _verdict_key(claim: Any) -> str:
    if isinstance(claim, dict):
        vr = claim.get("verification_result") or {}
        if isinstance(vr, dict):
            return str(vr.get("result") or claim.get("initial_assessment") or "").upper()
        return str(claim.get("initial_assessment") or "").upper()
    vr = getattr(claim, "verification_result", None) or {}
    if isinstance(vr, dict):
        return str(vr.get("result") or getattr(claim, "initial_assessment", "") or "").upper()
    return str(getattr(claim, "initial_assessment", "") or "").upper()


def _claim_text(claim: Any) -> str:
    if isinstance(claim, dict):
        return str(claim.get("claim_text") or "")
    return str(getattr(claim, "claim_text", "") or "")


def _timestamp(claim: Any) -> str:
    if isinstance(claim, dict):
        return str(claim.get("timestamp") or "")
    return str(getattr(claim, "timestamp", "") or "")


def _source_type(claim: Any) -> str:
    if isinstance(claim, dict):
        return str(claim.get("source_type") or "spoken")
    return str(getattr(claim, "source_type", "") or "spoken")


def compute_brand_safety_scores(
    video_id: str,
    claims: list[Any],
    *,
    press_release_flags: int = 0,
    ci_hit_rate: float = 0.0,
) -> BrandSafetyScores:
    """Derive agency SKU A scores from claim inventory + verification."""
    scores = BrandSafetyScores(
        video_id=video_id,
        scored_at=datetime.now(timezone.utc).isoformat(),
        press_release_flags=press_release_flags,
        ci_hit_rate=ci_hit_rate,
    )

    high_flags: list[dict[str, Any]] = []
    disclosure_ms = 0

    for claim in claims or []:
        text = _claim_text(claim)
        st = _source_type(claim)
        ts = _timestamp(claim)
        verdict = _verdict_key(claim)
        visual = is_visual_only_claim(st)

        if visual:
            scores.visual_only_claim_count += 1
            if verdict in _HIGH_RISK_VERDICTS or "FALSE" in verdict:
                scores.visual_only_high_risk_count += 1
                high_flags.append(
                    {
                        "claim": text[:200],
                        "verdict": verdict,
                        "category": "visual_only_high_risk",
                        "timestamp": ts,
                        "source_type": st,
                    }
                )

        if _DISCLOSURE_RE.search(text):
            scores.sponsor_read_detected = True
            if visual:
                on_ms = 0
                if isinstance(claim, dict):
                    on_ms = int(claim.get("on_screen_ms") or 0)
                disclosure_ms += max(on_ms, 500)

        if visual and _CREDENTIAL_RE.search(text):
            scores.credential_flash_events.append(
                CredentialFlashEvent(timestamp=ts, claim_text=text[:200], source_type=st)
            )

        bucket = "low"
        if verdict in _HIGH_RISK_VERDICTS:
            bucket = "high"
        elif "UNCERTAIN" in verdict or "MIXED" in verdict:
            bucket = "medium"
        scores.claim_risk_buckets[bucket] = scores.claim_risk_buckets.get(bucket, 0) + 1

    scores.disclosure_on_screen_ms = disclosure_ms
    scores.top_flags = high_flags[:5]

    high_n = scores.claim_risk_buckets.get("high", 0)
    med_n = scores.claim_risk_buckets.get("medium", 0)
    if high_n >= 2 or scores.visual_only_high_risk_count >= 1:
        scores.overall_risk = "high"
        scores.recommended_action = "reject"
    elif high_n >= 1 or med_n >= 3 or scores.visual_only_high_risk_count >= 1:
        scores.overall_risk = "medium"
        scores.recommended_action = "legal_review_before_spend"
    else:
        scores.overall_risk = "low"
        scores.recommended_action = "approve"

    if scores.sponsor_read_detected and scores.disclosure_on_screen_ms < 1000:
        scores.undisclosed_affiliate_risk = "elevated"
        if scores.recommended_action == "approve":
            scores.recommended_action = "legal_review_before_spend"

    return scores


def persist_brand_safety_scores(
    video_id: str,
    claims: list[Any],
    out_dir: Path | str,
    **kwargs: Any,
) -> Path:
    """Write `brand_safety_scores.json` beside report outputs."""
    out = Path(out_dir)
    scores = compute_brand_safety_scores(video_id, claims, **kwargs)
    path = out / "brand_safety_scores.json"
    scores.write_json(path)
    return path
