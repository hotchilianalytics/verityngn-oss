"""Multimodal claim extraction arm for modality ablation (claims only)."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_OFFLINE_FIXTURE: List[Dict[str, Any]] = [
    {
        "claim_text": "The product was clinically tested in a peer-reviewed trial.",
        "timestamp": "00:45",
        "source_type": "spoken",
        "context": "Spoken claim overlapping transcript arm.",
    },
    {
        "claim_text": "Harvard researchers validated the formula.",
        "timestamp": "01:12",
        "source_type": "spoken",
        "context": "Spoken authority claim.",
    },
    {
        "claim_text": "On-screen graphic shows 97% success rate.",
        "timestamp": "01:40",
        "source_type": "visual_text",
        "context": "OCR / overlay not in spoken transcript.",
    },
    {
        "claim_text": "Chart labeled FDA approved appears behind the speaker.",
        "timestamp": "02:20",
        "source_type": "chart",
        "context": "Visual chart claim absent from captions.",
    },
    {
        "claim_text": "Customers lose weight in two weeks without diet changes.",
        "timestamp": "02:05",
        "source_type": "spoken",
        "context": "Spoken efficacy claim.",
    },
]


def _extract_video_id(url: str) -> Optional[str]:
    if not url:
        return None
    m = re.search(r"(?:v=|/shorts/|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


VISUAL_OR_SPOKEN = frozenset(
    {"spoken", "visual_text", "graphic", "chart", "demonstration"}
)


def _infer_source_type(claim: Dict[str, Any]) -> str:
    """Normalize modality; recover visual_* when LLM only marks Visual Text speaker."""
    raw = str(claim.get("source_type") or claim.get("modality") or "").strip().lower()
    if raw in VISUAL_OR_SPOKEN:
        return raw
    speaker_l = str(claim.get("speaker") or "").strip().lower()
    if any(
        tok in speaker_l
        for tok in (
            "visual text",
            "on-screen",
            "onscreen",
            "graphic",
            "chart",
            "slide",
            "exhibit",
            "ocr",
        )
    ):
        if "chart" in speaker_l or "slide" in speaker_l:
            return "chart"
        if "graphic" in speaker_l:
            return "graphic"
        return "visual_text"
    if raw and raw not in ("unknown", "none", "null", ""):
        return raw
    return "spoken"


def _normalize_claims(raw: List[Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for c in raw or []:
        if isinstance(c, dict):
            item = dict(c)
            item.setdefault("claim_text", str(c.get("text") or c.get("claim_text") or ""))
            item["source_type"] = _infer_source_type(item)
            item.setdefault("timestamp", c.get("timestamp") or "unknown")
            out.append(item)
        elif c:
            out.append(
                {
                    "claim_text": str(c),
                    "timestamp": "unknown",
                    "source_type": "spoken",
                }
            )
    return out


def _video_info_stub(video_id: str, title: str = "") -> Dict[str, Any]:
    return {
        "id": video_id,
        "title": title or f"Video {video_id}",
        "description": "",
        "duration": 0,
        "thumbnail": f"https://img.youtube.com/vi/{video_id}/0.jpg",
    }


def _fetch_video_info(youtube_url: str, video_id: str, title: str = "") -> Dict[str, Any]:
    try:
        import yt_dlp

        with yt_dlp.YoutubeDL(
            {"quiet": True, "no_warnings": True, "skip_download": True, "ignoreerrors": True}
        ) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
        if info:
            return info
    except Exception as exc:  # noqa: BLE001
        logger.warning("yt-dlp metadata failed: %s", exc)
    return _video_info_stub(video_id, title)


async def _extract_multimodal_claims(
    youtube_url: str, video_id: str, video_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Use the same YouTube multimodal extract path as the analysis pipeline."""
    from verityngn.workflows.analysis import (
        extract_claims_with_gemini_multimodal_youtube_url,
        extract_claims_with_gemini_multimodal_youtube_url_segmented_vertex,
    )

    try:
        from verityngn.config.settings import USE_VERTEX_SEGMENTED_YOUTUBE
    except Exception:
        USE_VERTEX_SEGMENTED_YOUTUBE = True

    if USE_VERTEX_SEGMENTED_YOUTUBE:
        result = await extract_claims_with_gemini_multimodal_youtube_url_segmented_vertex(
            youtube_url, video_id, video_info
        )
    else:
        result = await extract_claims_with_gemini_multimodal_youtube_url(
            youtube_url, video_id, video_info
        )

    if not isinstance(result, dict) or result.get("error"):
        err = result.get("error") if isinstance(result, dict) else result
        logger.error("Multimodal claim extract failed: %s", err)
        return []
    return _normalize_claims(result.get("claims") or [])


def run_multimodal_claims_arm(
    *,
    out_dir: str,
    video_id: str = "",
    youtube_url: str = "",
    title: str = "",
    use_live_llm: bool = True,
) -> Dict[str, Any]:
    """Run multimodal claim extraction only; write claims_multimodal.json."""
    t0 = time.perf_counter()
    os.makedirs(out_dir, exist_ok=True)
    vid = video_id or _extract_video_id(youtube_url) or "unknown"
    url = youtube_url or (f"https://www.youtube.com/watch?v={vid}" if vid != "unknown" else "")

    video_info: Dict[str, Any] = _video_info_stub(vid, title)
    if not use_live_llm:
        claims = [dict(c) for c in _OFFLINE_FIXTURE]
        extract_error = None
    else:
        if not url:
            raise ValueError("multimodal arm requires youtube_url or video_id")
        video_info = _fetch_video_info(url, vid, title)
        try:
            claims = asyncio.run(_extract_multimodal_claims(url, vid, video_info))
            extract_error = None
        except Exception as exc:  # noqa: BLE001
            logger.exception("multimodal arm extract crashed")
            claims = []
            extract_error = str(exc)

    inventory = {
        "arm": "multimodal",
        "video_id": vid,
        "youtube_url": url,
        "title": title or video_info.get("title") or f"Video {vid}",
        "n_claims": len(claims),
        "claims": claims,
        "offline": not use_live_llm,
        "extract_error": extract_error,
    }
    claims_path = Path(out_dir) / "claims_multimodal.json"
    claims_path.write_text(json.dumps(inventory, indent=2, default=str), encoding="utf-8")

    md_lines = [
        f"# Multimodal claim inventory — {vid}",
        "",
        f"Claims: **{len(claims)}**",
        "",
    ]
    for i, c in enumerate(claims, 1):
        md_lines.append(
            f"{i}. [{c.get('timestamp', '?')}] {c.get('claim_text', '')} "
            f"(source_type={c.get('source_type', 'unknown')})"
        )
    md_path = Path(out_dir) / "claims_multimodal.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    return {
        "status": "completed" if not extract_error else "failed",
        "arm": "multimodal",
        "video_id": vid,
        "out_dir": out_dir,
        "claims_path": str(claims_path),
        "markdown_path": str(md_path),
        "n_claims": len(claims),
        "claims": claims,
        "elapsed_sec": time.perf_counter() - t0,
        "offline": not use_live_llm,
        "extract_error": extract_error,
    }
