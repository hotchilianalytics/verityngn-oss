"""Ordered transcript provider chain with cost budget guard."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from verityngn.services.video.transcript_providers.asr_groq import GroqAsrProvider
from verityngn.services.video.transcript_providers.base import TranscriptResult, cues_to_vtt
from verityngn.services.video.transcript_providers.supadata import SupadataProvider

logger = logging.getLogger(__name__)


def provider_chain_from_env() -> List[str]:
    raw = os.getenv(
        "TRANSCRIPT_PROVIDERS",
        "cached,ytdlp,api,supadata,asr,gemini",
    ).strip()
    return [p.strip().lower() for p in raw.split(",") if p.strip()]


def max_cost_usd() -> float:
    try:
        return float(os.getenv("TRANSCRIPT_MAX_COST_USD", "0.05"))
    except ValueError:
        return 0.05


def fetch_via_providers(
    video_id: str,
    url: str = "",
    *,
    output_dir: str = "",
    lang: str = "en",
    providers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Try paid providers (supadata, asr) in order.

    Free paths (cached/ytdlp/api/gemini) remain in caption_fetch; this helper
    is invoked for the paid segment of the chain.
    Writes ``{video_id}.vendor.vtt`` on success (never clobbers ``.en.vtt``).
    """
    chain = providers or [p for p in provider_chain_from_env() if p in ("supadata", "asr", "asr_groq")]
    budget = max_cost_usd()
    spent = 0.0
    attempts: List[Dict[str, Any]] = []

    for name in chain:
        if spent >= budget:
            attempts.append({"provider": name, "skipped": True, "reason": "budget_exhausted"})
            continue
        if name == "supadata":
            prov = SupadataProvider()
            if not prov.available():
                attempts.append({"provider": name, "skipped": True, "reason": "no_api_key"})
                continue
            result = prov.fetch(video_id=video_id, url=url, lang=lang, mode="auto")
        elif name in ("asr", "asr_groq"):
            prov = GroqAsrProvider()
            if not prov.available():
                attempts.append({"provider": name, "skipped": True, "reason": "no_api_key"})
                continue
            result = prov.fetch(video_id=video_id, url=url, lang=lang)
        else:
            continue

        attempts.append(
            {
                "provider": name,
                "success": result.success,
                "latency_sec": result.latency_sec,
                "usd_estimate": result.usd_estimate,
                "error": result.error,
                "kind": result.kind,
            }
        )
        if not result.success:
            continue
        if spent + result.usd_estimate > budget and result.usd_estimate > 0:
            # Still accept if this is the only way — but log over-budget
            logger.warning(
                "Transcript provider %s usd=%.4f exceeds remaining budget %.4f; accepting",
                name,
                result.usd_estimate,
                budget - spent,
            )
        spent += result.usd_estimate
        vtt_path = _write_vendor_vtt(video_id, output_dir, result)
        return {
            "success": True,
            "text": result.text,
            "vtt_path": vtt_path,
            "source": result.source,
            "kind": result.kind,
            "latency_sec": result.latency_sec,
            "usd_estimate": result.usd_estimate,
            "attempts": attempts,
            "spent_usd": spent,
            "error": None,
        }

    return {
        "success": False,
        "text": "",
        "vtt_path": None,
        "source": "none",
        "kind": "none",
        "latency_sec": sum(a.get("latency_sec") or 0 for a in attempts),
        "usd_estimate": spent,
        "attempts": attempts,
        "spent_usd": spent,
        "error": "all paid providers failed or skipped",
    }


def _write_vendor_vtt(video_id: str, output_dir: str, result: TranscriptResult) -> Optional[str]:
    if not output_dir:
        return None
    from verityngn.services.video.caption_fetch import analysis_dir_for, canonical_vtt_path

    # Never clobber official captions
    if canonical_vtt_path(output_dir, video_id).is_file():
        logger.info("Skipping vendor.vtt write — official .en.vtt present")
        return str(canonical_vtt_path(output_dir, video_id))

    analysis = analysis_dir_for(output_dir, video_id)
    analysis.mkdir(parents=True, exist_ok=True)
    path = analysis / f"{video_id}.vendor.vtt"
    vtt = result.vtt or cues_to_vtt(result.cues)
    if not vtt.strip().upper().startswith("WEBVTT"):
        vtt = "WEBVTT\n\n" + vtt
    path.write_text(vtt, encoding="utf-8")
    return str(path)
