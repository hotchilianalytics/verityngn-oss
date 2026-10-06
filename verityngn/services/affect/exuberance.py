"""Exuberance composite: arousal × valence around a claim window."""
from __future__ import annotations

from typing import Optional

from verityngn.services.affect.prosody import ProsodyFeatures


def exuberance_score(
    prosody: ProsodyFeatures,
    text_sentiment: float,
    *,
    baseline_f0: Optional[float] = None,
    baseline_energy: Optional[float] = None,
) -> float:
    """
    Returns exuberance in approximately [0, 1].

    Arousal from elevated F0 / energy / rate vs optional baseline;
    valence from text sentiment proxy. Research signal only.
    """
    f0 = prosody.f0_mean
    energy = prosody.energy_mean
    rate = prosody.rate_sps

    arousal_parts = []
    if f0 == f0:  # not NaN
        base = baseline_f0 if baseline_f0 and baseline_f0 == baseline_f0 else 120.0
        arousal_parts.append(min(1.0, max(0.0, (f0 - base) / 80.0 + 0.5)))
    if energy == energy:
        base_e = baseline_energy if baseline_energy and baseline_energy == baseline_energy else 0.05
        arousal_parts.append(min(1.0, max(0.0, energy / max(base_e * 3.0, 1e-6))))
    if rate == rate:
        arousal_parts.append(min(1.0, max(0.0, rate / 8.0)))

    arousal = sum(arousal_parts) / len(arousal_parts) if arousal_parts else 0.5
    valence = (float(text_sentiment) + 1.0) / 2.0  # map [-1,1] -> [0,1]
    # exuberance emphasizes positive high-arousal; still defined for negative valence
    return float(max(0.0, min(1.0, 0.6 * arousal + 0.4 * valence)))
