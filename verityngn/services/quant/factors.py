"""PIT media-factor panel builder — modeled on hca-qngn build_fundamental_factors.

Rules:
- merge_asof direction='backward' only
- no bfill
- same-day cross-sectional z per date
- never fillna(0) on sparse coverage
"""
from __future__ import annotations

from typing import Any, Optional
import json
from pathlib import Path
import math
import statistics


def _cs_z(values: list[Optional[float]]) -> list[Optional[float]]:
    valid = [v for v in values if v is not None and v == v]
    if len(valid) < 2:
        return values
    mu = statistics.fmean(valid)
    sd = statistics.pstdev(valid) or 1.0
    out: list[Optional[float]] = []
    for v in values:
        if v is None or v != v:
            out.append(None)  # preserve missing — do NOT fillna(0)
        else:
            out.append((v - mu) / sd)
    return out


def merge_asof_backward(
    events: list[dict[str, Any]],
    features: list[dict[str, Any]],
    *,
    event_ts_key: str = "event_date",
    feature_ts_key: str = "asof_available",
    ticker_key: str = "ticker",
) -> list[dict[str, Any]]:
    """
    For each event, attach the latest feature row with asof <= event_ts for that ticker.
    No forward fill / bfill.
    """
    feats_by_ticker: dict[str, list[dict[str, Any]]] = {}
    for f in features:
        t = str(f.get(ticker_key) or "").upper()
        feats_by_ticker.setdefault(t, []).append(f)
    for t in feats_by_ticker:
        feats_by_ticker[t].sort(key=lambda r: str(r.get(feature_ts_key) or ""))

    out = []
    for ev in events:
        t = str(ev.get(ticker_key) or "").upper()
        ets = str(ev.get(event_ts_key) or "")
        candidates = [f for f in feats_by_ticker.get(t, []) if str(f.get(feature_ts_key) or "") <= ets]
        if not candidates:
            row = {**ev, "feature_matched": False}
            out.append(row)
            continue
        best = candidates[-1]
        merged = {**ev, **{k: v for k, v in best.items() if k not in ev}, "feature_matched": True}
        # Enforce causal cutoff explicitly
        if str(best.get(feature_ts_key) or "") > ets:
            raise ValueError(f"Leakage: feature asof {best.get(feature_ts_key)} after event {ets}")
        out.append(merged)
    return out


def build_media_factor_panel(
    events: list[dict[str, Any]],
    features: list[dict[str, Any]],
    *,
    factor_keys: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    factor_keys = factor_keys or [
        "exuberance_mean",
        "mediasphere_velocity",
        "delivery_risk",
        "congruence",
        "sympathetic_arousal",
    ]
    merged = merge_asof_backward(events, features)
    # Cross-sectional z by event_date across tickers
    by_date: dict[str, list[dict[str, Any]]] = {}
    for r in merged:
        by_date.setdefault(str(r.get("event_date") or ""), []).append(r)

    panel = []
    for d, group in by_date.items():
        for fk in factor_keys:
            raw = []
            for r in group:
                v = r.get(fk)
                try:
                    raw.append(float(v) if v is not None and v == v else None)
                except (TypeError, ValueError):
                    raw.append(None)
            zvals = _cs_z(raw)
            for r, z in zip(group, zvals):
                r = dict(r)
                r[f"{fk}_z"] = z
                panel.append(r) if fk == factor_keys[-1] else None
        # attach all z keys onto each row once
        # redo cleanly:
    panel = []
    for d, group in by_date.items():
        zmaps: dict[str, list[Optional[float]]] = {}
        for fk in factor_keys:
            raw = []
            for r in group:
                v = r.get(fk)
                try:
                    raw.append(float(v) if v is not None and float(v) == float(v) else None)
                except (TypeError, ValueError):
                    raw.append(None)
            zmaps[fk] = _cs_z(raw)
        for i, r in enumerate(group):
            row = dict(r)
            row["date"] = d
            preds = []
            for fk in factor_keys:
                row[f"{fk}_z"] = zmaps[fk][i]
                if zmaps[fk][i] is not None:
                    preds.append(zmaps[fk][i])
            # Composite prediction = mean of available z's (skip missing)
            row["prediction"] = (sum(preds) / len(preds)) if preds else None
            # Target: surprise direction / pct if present
            if "surprise_pct" in row:
                row["y"] = float(row["surprise_pct"])
            panel.append(row)
    return panel


def write_panel(panel: list[dict[str, Any]], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in panel:
            f.write(json.dumps(r) + "\n")
    return path
