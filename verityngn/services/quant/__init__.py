"""Quant sleeve — media-factor builders and hygiene gates (hca-qngn-aligned)."""
from __future__ import annotations

from verityngn.services.quant.hygiene import HygieneResult, run_factor_hygiene
from verityngn.services.quant.ic import daily_rank_ic, event_time_ic, ic_summary
from verityngn.services.quant.signal_quality import score_signal_quality

__all__ = [
    "HygieneResult",
    "run_factor_hygiene",
    "daily_rank_ic",
    "event_time_ic",
    "ic_summary",
    "score_signal_quality",
]

# Exact gate thresholds (mirrored from hca-qngn factor-research-hygiene)
ICIR_FLOOR = 0.40
FRAC_IC_POS = 0.55
WEEKLY_JACCARD_MAX = 0.25
NEUTRALIZATION_RATIO = 0.5  # resid ICIR >= 0.5 * raw ICIR
DSR_MIN = 0.95
COST_BPS_HYGIENE = 10
COST_BPS_PROMOTE = 20
