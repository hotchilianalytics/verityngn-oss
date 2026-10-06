"""Nuisance residualizer — strip n_claims / duration / venue from factor values.

The residual is what may enter a market test. Raw values stay on the panel
for QA. Never fillna(0). Ordinary least squares via numpy if present, else
a two-pass mean/slope fallback on a single covariate.
"""
from __future__ import annotations

import math
from typing import Any, Optional


NUISANCE_KEYS = ("n_claims", "duration_sec", "n_segments", "days_to_print")


def _finite(v: Any) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f or math.isinf(f):
        return None
    return f


def _ols_resid(y: list[float], X: list[list[float]]) -> list[float]:
    """y = Xb + e. Return residuals. X should already include intercept column.

    Requires numpy. A silent single-covariate fallback previously under-residualized
    multi-covariate designs and left duration leak inflated.
    """
    n = len(y)
    k = len(X[0]) if X else 0
    if n < k or k == 0:
        return list(y)
    try:
        import numpy as np  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise RuntimeError(
            "numpy is required for multi-covariate residualization; "
            "refusing silent single-covariate fallback"
        ) from e

    xa = np.asarray(X, dtype=float)
    ya = np.asarray(y, dtype=float)
    beta, *_ = np.linalg.lstsq(xa, ya, rcond=None)
    pred = xa @ beta
    return [float(a - b) for a, b in zip(ya, pred)]

def residualize_rows(
    rows: list[dict[str, Any]],
    *,
    factor_key: str,
    nuisance_keys: tuple[str, ...] = NUISANCE_KEYS,
    residual_key: Optional[str] = None,
    venue_key: str = "venue",
) -> list[dict[str, Any]]:
    """Attach `{factor_key}_resid` (or residual_key) on a copy of each row.

    Rows missing the factor are passed through unchanged (no fill).
    """
    residual_key = residual_key or f"{factor_key}_resid"
    usable: list[int] = []
    y: list[float] = []
    raw_x: list[list[float]] = []
    venue_vals = sorted(
        {
            str(r.get(venue_key) or "")
            for r in rows
            if r.get(venue_key) not in (None, "")
        }
    )
    venue_index = {v: i for i, v in enumerate(venue_vals)}

    # Only use nuisance columns that are finite on every row that has the factor.
    # Missing → 0.0 was biasing leak (treated unknown days_to_print as zero).
    factor_rows: list[tuple[int, dict[str, Any]]] = []
    for i, r in enumerate(rows):
        fv = _finite(r.get(factor_key))
        if fv is None:
            continue
        factor_rows.append((i, r))
        usable.append(i)
        y.append(fv)

    complete_keys = [
        k
        for k in nuisance_keys
        if factor_rows and all(_finite(r.get(k)) is not None for _, r in factor_rows)
    ]

    for i, r in factor_rows:
        rowx = [1.0]
        for k in complete_keys:
            rowx.append(float(_finite(r.get(k))))  # type: ignore[arg-type]
        if venue_index and r.get(venue_key):
            onehot = [0.0] * len(venue_index)
            onehot[venue_index[str(r.get(venue_key))]] = 1.0
            rowx.extend(onehot)
        raw_x.append(rowx)

    out = [dict(r) for r in rows]
    if len(y) < 3:
        for i in usable:
            out[i][residual_key] = None
            out[i][f"{factor_key}_resid_reason"] = "n<3"
        return out

    # Drop all-zero columns except intercept
    ncol = len(raw_x[0])
    keep = [0]
    for j in range(1, ncol):
        col = [row[j] for row in raw_x]
        if sum(abs(v) for v in col) > 1e-12 and max(col) - min(col) > 1e-12:
            keep.append(j)
    X = [[row[j] for j in keep] for row in raw_x]
    resid = _ols_resid(y, X)
    for i, e in zip(usable, resid):
        out[i][residual_key] = round(float(e), 6)
        out[i][f"{factor_key}_raw"] = out[i].get(factor_key)
    return out


def residualize_panel(
    rows: list[dict[str, Any]],
    factor_keys: list[str],
    *,
    nuisance_keys: tuple[str, ...] = NUISANCE_KEYS,
) -> list[dict[str, Any]]:
    out = [dict(r) for r in rows]
    for key in factor_keys:
        out = residualize_rows(out, factor_key=key, nuisance_keys=nuisance_keys)
    return out
