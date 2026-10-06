"""Aggregate deception_risk from Tier-1 measured features (+ optional vendor)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
import statistics

from verityngn.services.deception.congruence import band_from_score, baseline_deviation, text_voice_divergence


DISCLAIMER = (
    "deception_risk is a delivery / congruence band derived from measured speech-text "
    "features. It is not a lie detector and must not be presented as a finding that a "
    "named person is lying."
)


@dataclass
class DeceptionRiskResult:
    video_id: str
    segments: list[dict[str, Any]] = field(default_factory=list)
    overall_band: str = "low"
    overall_score: float = 0.0
    vendor_constructs: list[dict[str, Any]] = field(default_factory=list)
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "segments": self.segments,
            "overall_band": self.overall_band,
            "overall_score": self.overall_score,
            "vendor_constructs": self.vendor_constructs,
            "disclaimer": self.disclaimer,
            # Explicit alias for API clarity — never "lie_score"
            "label": "deception_risk",
        }


def assess_deception_risk(
    affect: dict[str, Any],
    *,
    vendor_results: Optional[list[dict[str, Any]]] = None,
) -> DeceptionRiskResult:
    video_id = str(affect.get("video_id") or "unknown")
    segs_in = affect.get("segments") or []

    # Baseline from segment means
    jitters = [s.get("prosody", {}).get("jitter") for s in segs_in if isinstance(s, dict)]
    jitters = [j for j in jitters if isinstance(j, (int, float)) and j == j]
    j_mean = statistics.fmean(jitters) if jitters else 0.02
    j_std = statistics.pstdev(jitters) if len(jitters) > 1 else 0.01

    out_segs: list[dict[str, Any]] = []
    scores: list[float] = []
    for s in segs_in:
        if not isinstance(s, dict):
            continue
        sent = float(s.get("text_sentiment") or 0.0)
        ex = s.get("exuberance")
        ex_f = float(ex) if isinstance(ex, (int, float)) and ex == ex else 0.5
        div = text_voice_divergence(sent, ex_f)
        dis_rate = float((s.get("disfluency") or {}).get("rate") or 0.0)
        jitter = (s.get("prosody") or {}).get("jitter")
        j_dev = baseline_deviation(float(jitter) if jitter == jitter else j_mean, j_mean, j_std)
        # Weighted Tier-1 score
        score = min(1.0, 0.45 * div + 0.35 * min(1.0, dis_rate * 10.0) + 0.20 * min(1.0, j_dev / 3.0))
        band = band_from_score(score)
        scores.append(score)
        out_segs.append(
            {
                "claim_id": s.get("claim_id"),
                "timestamp_sec": s.get("timestamp_sec"),
                "divergence": div,
                "disfluency_rate": dis_rate,
                "jitter_z": j_dev,
                "deception_risk_score": score,
                "deception_risk_band": band,
                "flags": {
                    "congruence": "low" if div > 0.5 else "aligned",
                    "conviction": "shaky" if dis_rate > 0.08 else "steady",
                    "delivery_risk": band,
                },
            }
        )

    overall = float(sum(scores) / len(scores)) if scores else 0.0
    return DeceptionRiskResult(
        video_id=video_id,
        segments=out_segs,
        overall_band=band_from_score(overall),
        overall_score=overall,
        vendor_constructs=list(vendor_results or []),
    )
