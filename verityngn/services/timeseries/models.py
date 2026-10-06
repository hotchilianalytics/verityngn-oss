"""Simple baseline models (logit / fallback majority) without heavy deps required."""
from __future__ import annotations

from typing import Any, Optional, Sequence


class MajorityModel:
    def __init__(self, majority: int) -> None:
        self.majority = majority

    def predict(self, x: Sequence[float]) -> int:
        return self.majority


class LogitModel:
    """Tiny gradient-descent logistic regression (numpy optional)."""

    def __init__(self, weights: list[float], bias: float) -> None:
        self.weights = weights
        self.bias = bias

    def predict_proba(self, x: Sequence[float]) -> float:
        z = self.bias + sum(w * float(v) for w, v in zip(self.weights, x))
        # stable sigmoid
        if z >= 0:
            ez = pow(2.718281828, -z)
            return 1.0 / (1.0 + ez)
        ez = pow(2.718281828, z)
        return ez / (1.0 + ez)

    def predict(self, x: Sequence[float]) -> int:
        return 1 if self.predict_proba(x) >= 0.5 else 0


def fit_baseline_logit(
    rows: list[dict[str, Any]],
    *,
    feature_keys: list[str],
    label_key: str,
    steps: int = 200,
    lr: float = 0.2,
) -> Optional[Any]:
    if not rows:
        return None
    xs = [[float(r.get(k) or 0.0) for k in feature_keys] for r in rows]
    ys = [int(r[label_key]) for r in rows]
    if len(set(ys)) < 2:
        return MajorityModel(max(set(ys), key=ys.count))

    try:
        import numpy as np

        X = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
        # standardize
        mu = X.mean(axis=0)
        sd = X.std(axis=0) + 1e-6
        Xn = (X - mu) / sd
        w = np.zeros(X.shape[1])
        b = 0.0
        for _ in range(steps):
            z = Xn @ w + b
            p = 1.0 / (1.0 + np.exp(-z))
            err = p - y
            w -= lr * (Xn.T @ err) / len(y)
            b -= lr * float(err.mean())
        # fold standardization into weights for predict on raw x
        w_raw = (w / sd).tolist()
        b_raw = float(b - (w / sd) @ mu)
        return LogitModel(w_raw, b_raw)
    except ImportError:
        # Fallback: majority
        return MajorityModel(max(set(ys), key=ys.count))
