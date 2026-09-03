"""Per-arm cost and latency telemetry for sufficiency routing (T-ABL-007)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Published rates (2026-09-02) — override via env for calibration
_DEFAULT_USD_PER_1M_INPUT = float(os.getenv("VN_USD_PER_1M_INPUT", "0.15"))
_DEFAULT_USD_PER_1M_OUTPUT = float(os.getenv("VN_USD_PER_1M_OUTPUT", "0.60"))
# Multimodal video understanding ~290 tokens/s of video (video_segmentation.py)
TOKENS_PER_VIDEO_SEC = float(os.getenv("VN_TOKENS_PER_VIDEO_SEC", "290"))


def estimate_llm_usd(
    input_tokens: int = 0,
    output_tokens: int = 0,
    *,
    usd_per_1m_input: Optional[float] = None,
    usd_per_1m_output: Optional[float] = None,
) -> float:
    i = usd_per_1m_input if usd_per_1m_input is not None else _DEFAULT_USD_PER_1M_INPUT
    o = usd_per_1m_output if usd_per_1m_output is not None else _DEFAULT_USD_PER_1M_OUTPUT
    return (input_tokens / 1_000_000.0) * i + (output_tokens / 1_000_000.0) * o


def estimate_multimodal_input_tokens(duration_sec: float) -> int:
    """Heuristic input tokens for full-arm video understanding."""
    if duration_sec <= 0:
        return 0
    return int(duration_sec * TOKENS_PER_VIDEO_SEC)


def estimate_transcript_tokens(transcript_chars: int) -> int:
    """Rough chars→tokens (~4 chars/token)."""
    return max(0, transcript_chars // 4)


def build_arm_cost(
    *,
    arm: str,
    latency_sec: float,
    n_llm_calls: int = 1,
    input_tokens: int = 0,
    output_tokens: int = 0,
    transcript_chars_fetched: int = 0,
    transcript_chars_used: int = 0,
    transcript_usd: float = 0.0,
    duration_sec: float = 0.0,
    truncated: bool = False,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    llm_usd = estimate_llm_usd(input_tokens, output_tokens)
    payload: Dict[str, Any] = {
        "arm": arm,
        "latency_sec": round(latency_sec, 3),
        "n_llm_calls": n_llm_calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "transcript_chars_fetched": transcript_chars_fetched,
        "transcript_chars_used": transcript_chars_used,
        "truncated": truncated,
        "transcript_usd": round(transcript_usd, 6),
        "llm_usd_estimate": round(llm_usd, 6),
        "usd_estimate": round(transcript_usd + llm_usd, 6),
        "duration_sec": duration_sec,
    }
    if extra:
        payload.update(extra)
    return payload


def write_arm_cost(out_dir: str, cost: Dict[str, Any], name: str = "arm_cost.json") -> str:
    path = Path(out_dir) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cost, indent=2, default=str), encoding="utf-8")
    return str(path)
