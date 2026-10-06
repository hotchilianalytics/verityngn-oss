"""Signal-quality loss L — the loop objective for the Predictions sleeve.

L = w1*(1-Fidelity) + w2*NuisanceLeak + w3*(1-Power) + w4*(1-ICIRnorm) + w5*DeflationGap

Weights default to (0.30, 0.30, 0.20, 0.15, 0.05). Keep an iteration only if L
strictly decreases. Stop when L < 0.25 and NuisanceLeak < 0.2 and Power >= 1.

Constants (missing sensors filled with 0.5) count as fidelity zero.
"""
from __future__ import annotations

import math
from typing import Any, Optional

from verityngn.services.quant.deflated_sharpe import deflated_sharpe_probability
from verityngn.services.quant.ic import spearman
from verityngn.services.quant.nuisance import NUISANCE_KEYS


DEFAULT_WEIGHTS = (0.30, 0.30, 0.20, 0.15, 0.05)
RHO_TARGET = 0.20
N_REQUIRED_RHO20 = 194  # 80% power, two-sided alpha=0.05, Fisher-z
ICIR_FLOOR = 0.40
FIDELITY_FLOOR = 0.60
STOP_L = 0.25
STOP_NUISANCE = 0.20

PROXY_SOURCES = {
    "prosody_proxy",
    "offline_proxy",
    "missing_audio",
    "synthetic",
    "hash_seeded",
    "text_proxy",
}


def n_required(rho: float = RHO_TARGET, *, power: float = 0.80, alpha: float = 0.05) -> int:
    """Fisher-z sample size for Spearman rho (two-sided)."""
    if abs(rho) < 1e-6:
        return 10**9
    z_a = 1.95996398454  # N^{-1}(1-alpha/2)
    z_b = 0.841621233573  # N^{-1}(power)
    z = 0.5 * math.log((1.0 + rho) / (1.0 - rho))
    return int(math.ceil(((z_a + z_b) / z) ** 2 + 3.0))


def _finite(v: Any) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f or math.isinf(f):
        return None
    return f


def fidelity_of_row(row: dict[str, Any]) -> float:
    """Fraction of named sensor inputs that are measured.

    Inputs inspected: audio_source, gemini_source, vision_source,
    sympathetic_arousal presence, asr_source. Missing / proxy / defaulted
    constant → 0. Present measured → 1.
    """
    scores: list[float] = []

    def _src(key: str, measured_ok: tuple[str, ...] = ()) -> None:
        src = str(row.get(key) or "")
        if not src:
            scores.append(0.0)
            return
        if src in PROXY_SOURCES:
            scores.append(0.0)
            return
        if measured_ok:
            if src in measured_ok or src.startswith("measured"):
                scores.append(1.0)
            else:
                # Unknown tag — do NOT credit (was accidentally scoring 1.0)
                scores.append(0.0)
            return
        scores.append(1.0)

    _src("audio_source", ("audeering_wav2vec2", "prosody", "opensmile"))
    _src("gemini_source", ("gemini",))
    _src(
        "vision_source",
        ("mediapipe_face_landmarker", "pyfeat_detectorv2", "openface3", "pyvhr"),
    )
    _src("asr_source", ("faster_whisper", "whisper", "yt_captions"))

    ar = row.get("sympathetic_arousal")
    scores.append(1.0 if _finite(ar) is not None else 0.0)

    live = row.get("live_gemini")
    if live is False:
        # override gemini_source credit
        if scores:
            scores[1] = 0.0
    elif live is True:
        if len(scores) > 1:
            scores[1] = 1.0

    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def fidelity(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    return sum(fidelity_of_row(r) for r in rows) / len(rows)


def nuisance_leak(
    rows: list[dict[str, Any]],
    *,
    factor_key: str = "s01_congruence",
    nuisance_keys: tuple[str, ...] = NUISANCE_KEYS,
) -> dict[str, Any]:
    ys = [_finite(r.get(factor_key)) for r in rows]
    best = 0.0
    by: dict[str, Optional[float]] = {}
    for nk in nuisance_keys:
        xs = [_finite(r.get(nk)) for r in rows]
        pair = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
        if len(pair) < 3:
            by[nk] = None
            continue
        rho = spearman([p[0] for p in pair], [p[1] for p in pair])
        if rho != rho:
            by[nk] = None
            continue
        by[nk] = round(float(rho), 4)
        best = max(best, abs(rho))
    return {"max_abs": round(best, 4), "by_nuisance": by, "factor_key": factor_key}


def power_score(n_events: int, *, rho_target: float = RHO_TARGET) -> dict[str, Any]:
    need = n_required(rho_target)
    p = min(1.0, n_events / max(1, need))
    return {"n_events": n_events, "n_required": need, "rho_target": rho_target, "power": round(p, 4)}


def icir_norm(icir: Optional[float], *, floor: float = ICIR_FLOOR) -> float:
    if icir is None or icir != icir:
        return 0.0
    return float(min(abs(icir) / floor, 1.0))


def deflation_gap(
    *,
    observed_sharpe: float = 0.0,
    n_obs: int,
    n_trials: int,
) -> dict[str, Any]:
    dsr = deflated_sharpe_probability(observed_sharpe, n_obs=max(n_obs, 2), n_trials=max(n_trials, 1))
    return {"dsr": round(dsr, 6), "deflation_gap": round(1.0 - dsr, 6), "n_trials": n_trials, "n_obs": n_obs}


def score_signal_quality(
    rows: list[dict[str, Any]],
    *,
    factor_key: str = "s01_congruence",
    icir: Optional[float] = None,
    n_events: Optional[int] = None,
    n_trials: int = 13,
    observed_sharpe: float = 0.0,
    weights: tuple[float, ...] = DEFAULT_WEIGHTS,
) -> dict[str, Any]:
    fid = fidelity(rows)
    leak = nuisance_leak(rows, factor_key=factor_key)
    n_ev = n_events if n_events is not None else sum(1 for r in rows if r.get("car_h1") is not None)
    pwr = power_score(n_ev)
    icn = icir_norm(icir)
    dg = deflation_gap(observed_sharpe=observed_sharpe, n_obs=max(n_ev, 2), n_trials=n_trials)
    w1, w2, w3, w4, w5 = weights
    L = (
        w1 * (1.0 - fid)
        + w2 * leak["max_abs"]
        + w3 * (1.0 - pwr["power"])
        + w4 * (1.0 - icn)
        + w5 * dg["deflation_gap"]
    )
    stop = L < STOP_L and leak["max_abs"] < STOP_NUISANCE and pwr["power"] >= 1.0 - 1e-9
    return {
        "L": round(L, 6),
        "stop": stop,
        "weights": {"fidelity": w1, "nuisance": w2, "power": w3, "icir": w4, "deflation": w5},
        "fidelity": round(fid, 4),
        "nuisance_leak": leak,
        "power": pwr,
        "icir": icir,
        "icir_norm": round(icn, 4),
        "deflation": dg,
        "promote": "NO_PROMOTE",
        "instrument_only": fid < FIDELITY_FLOOR,
        "notes": (
            "Keep iteration only if L strictly decreases. "
            "A rise in ICIR that also raises NuisanceLeak is a rejection. "
            "NO_PROMOTE until stop conditions."
        ),
    }


def stamp_instrument_only(payload: dict[str, Any], fidelity_value: float) -> dict[str, Any]:
    out = dict(payload)
    if fidelity_value < FIDELITY_FLOOR:
        out["instrument_only"] = True
        out["promote"] = "NO_PROMOTE"
        out["fidelity"] = fidelity_value
    else:
        out["instrument_only"] = False
        out["fidelity"] = fidelity_value
    return out
