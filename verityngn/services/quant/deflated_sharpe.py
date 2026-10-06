"""Deflated Sharpe Ratio (Bailey & López de Prado) — DSR probability gate ≥ 0.95."""
from __future__ import annotations

from typing import Optional
import math


def deflated_sharpe_probability(
    observed_sharpe: float,
    *,
    n_obs: int,
    n_trials: int,
    skew: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
    """
    Approximate DSR as P(SR* > 0) under multiple-testing adjustment.

    Returns a probability in [0,1]. Gate: DSR >= 0.95.
    """
    if n_obs < 2 or n_trials < 1:
        return 0.0
    # Expected max SR under N(0,1) trials (Euler-Mascheroni approximation)
    em = 0.5772156649
    sr0 = (1.0 - em) * math.sqrt(2.0 * math.log(max(n_trials, 2))) + em * math.sqrt(
        2.0 * math.log(max(n_trials, 2))
    ) / (2.0 * math.log(max(n_trials, 2)))
    # Variance of SR estimator
    sr_var = (1.0 - skew * observed_sharpe + ((kurtosis - 1.0) / 4.0) * observed_sharpe**2) / (
        n_obs - 1
    )
    sr_var = max(sr_var, 1e-12)
    z = (observed_sharpe - sr0) / math.sqrt(sr_var)
    # Standard normal CDF
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def dsr_gate(observed_sharpe: float, n_obs: int, n_trials: int, *, min_p: float = 0.95) -> dict:
    p = deflated_sharpe_probability(observed_sharpe, n_obs=n_obs, n_trials=n_trials)
    return {
        "dsr": p,
        "pass": p >= min_p,
        "observed_sharpe": observed_sharpe,
        "n_obs": n_obs,
        "n_trials": n_trials,
        "threshold": min_p,
    }
