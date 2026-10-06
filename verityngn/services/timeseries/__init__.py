"""Timeseries sleeve — feature store, earnings join, leakage-safe event study."""
from __future__ import annotations

from verityngn.services.timeseries.store import FeatureStore
from verityngn.services.timeseries.event_study import EventStudyResult, run_event_study
from verityngn.services.timeseries.leakage import LeakageError, assert_causal, time_ordered_split

__all__ = [
    "FeatureStore",
    "EventStudyResult",
    "run_event_study",
    "LeakageError",
    "assert_causal",
    "time_ordered_split",
]
from verityngn.services.timeseries.returns import car, raw_h1  # noqa: F401
