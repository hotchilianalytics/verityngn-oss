"""Leakage guards for predictive pipelines."""
from __future__ import annotations

from typing import Any, Sequence, Tuple


class LeakageError(ValueError):
    """Raised when a feature would use information after the event cutoff."""


def assert_causal(feature_asof: str, event_ts: str, *, label: str = "feature") -> None:
    """Require feature_asof <= event_ts (lexicographic ISO dates/datetimes)."""
    if feature_asof > event_ts:
        raise LeakageError(
            f"Leakage: {label} asof={feature_asof} is after event_ts={event_ts}"
        )


def time_ordered_split(
    rows: Sequence[dict[str, Any]],
    *,
    ts_key: str = "ts",
    train: float = 0.6,
    val: float = 0.2,
) -> Tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Split by time order — never shuffle across events."""
    ordered = sorted(rows, key=lambda r: r.get(ts_key) or "")
    n = len(ordered)
    i_train = int(n * train)
    i_val = int(n * (train + val))
    return list(ordered[:i_train]), list(ordered[i_train:i_val]), list(ordered[i_val:])
