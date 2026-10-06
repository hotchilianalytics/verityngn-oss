"""Text–voice congruence and baseline deviation helpers."""
from __future__ import annotations

from typing import Any


def text_voice_divergence(text_sentiment: float, exuberance: float) -> float:
    """
    High when text is negative but delivery is high-arousal/positive (or inverse).
    Both inputs roughly in [-1,1] / [0,1]; returns [0,1].
    """
    # map exuberance [0,1] to [-1,1]
    delivery = exuberance * 2.0 - 1.0 if exuberance == exuberance else 0.0
    return float(min(1.0, abs(text_sentiment - delivery) / 2.0))


def baseline_deviation(value: float, baseline_mean: float, baseline_std: float) -> float:
    if baseline_std is None or baseline_std != baseline_std or baseline_std < 1e-9:
        return 0.0
    if value != value:
        return 0.0
    return float(abs(value - baseline_mean) / baseline_std)


def band_from_score(score: float) -> str:
    """Map [0,1] risk score to band. Language: delivery_risk, not lying."""
    if score < 0.33:
        return "low"
    if score < 0.66:
        return "moderate"
    return "elevated"
