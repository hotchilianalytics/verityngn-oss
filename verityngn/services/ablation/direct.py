"""DR-direct arm: grounded risk research without claims_breakdown inventory."""
from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Full transcript budget for light arm (was 12k — confounded T-ABL-001/005).
# Override with VN_LIGHT_TRANSCRIPT_MAX_CHARS; 0 or negative = no cap.
_DEFAULT_TRANSCRIPT_MAX = int(os.getenv("VN_LIGHT_TRANSCRIPT_MAX_CHARS", "0"))

_DIRECT_PROMPT = """You are VerityNgn Risk-Abatement Agent.

Analyze the provided video context (metadata, optional transcript excerpts, and any
attached multimodal cues). Produce a forensic **claim-level risk** briefing for
disclosure risk, delivery risk, brand-safety / sponsor-readiness, and authority-
fabrication patterns.

CRITICAL STANDARDS:
1. Do NOT frame this as a lie detector or moral "truthfulness" score.
2. Prefer risk language: Supported / Contested / Unresolved evidence for claims.
3. Every major deduction MUST end with [Reference: <URL>] or
   [Reference: Currently Claim is Unverified].
4. Call out press-release-shaped sources and self-promotional loops when suspected.
5. Structure with clear markdown headings: Executive risk summary, Key contested
   claims, Evidence gaps, Recommended abatements.

VIDEO CONTEXT JSON follows.
"""


def _extract_video_id_from_url(url: str) -> Optional[str]:
    if not url:
        return None
    m = re.search(r"(?:v=|/shorts/|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


def _cap_transcript(text: str, max_chars: Optional[int] = None) -> tuple[str, int, bool]:
    """Return (used_text, fetched_chars, truncated)."""
    fetched = len(text or "")
    limit = _DEFAULT_TRANSCRIPT_MAX if max_chars is None else max_chars
    if limit is None or limit <= 0 or fetched <= limit:
        return text or "", fetched, False
    return (text or "")[:limit], fetched, True


def build_direct_payload(
    *,
    video_id: str,
    title: str = "",
    description: str = "",
    transcript: str = "",
    youtube_url: str = "",
    video_path: str = "",
    max_transcript_chars: Optional[int] = None,
) -> Dict[str, Any]:
    """Minimal payload — intentionally has empty claims_breakdown (no inventory)."""
    used, fetched, truncated = _cap_transcript(transcript, max_transcript_chars)
    return {
        "video_id": video_id,
        "title": title or f"Video {video_id}",
        "description": (description or "")[:4000],
        "youtube_url": youtube_url,
        "video_path": video_path,
        "transcript_excerpt": used,
        "transcript_chars_fetched": fetched,
        "transcript_chars_used": len(used),
        "transcript_truncated": truncated,
        "claims_breakdown": [],  # explicit: no pipeline inventory
        "risk_framing": "disclosure_delivery_brand_safety",
        "ablation_arm": "dr_direct",
    }


def _try_load_transcript(video_id: str, video_path: str = "") -> str:
    """Best-effort: sidecar VTT, unified caption fetch, or sibling text files."""
    from verityngn.services.video.caption_fetch import fetch_and_cache_vtt, vtt_to_text

    if video_path:
        p = Path(video_path)
        for ext in (".vtt", ".srt", ".txt"):
            sidecar = p.with_suffix(ext)
            if sidecar.is_file() and sidecar.stat().st_size > 20:
                raw = sidecar.read_text(encoding="utf-8", errors="ignore")
                return vtt_to_text(raw) if ext == ".vtt" else raw

    for base in (Path("outputs") / video_id, Path("outputs"), Path("downloads"), Path(".")):
        for name in (
            f"{video_id}.en.vtt",
            f"{video_id}.vendor.vtt",
            f"{video_id}.gemini.vtt",
            f"{video_id}.vtt",
            f"{video_id}.txt",
        ):
            c = base / "analysis" / name if (base / "analysis").is_dir() else base / name
            if not c.is_file():
                c = base / "analysis" / name
            if c.is_file() and c.stat().st_size > 20:
                raw = c.read_text(encoding="utf-8", errors="ignore")
                return vtt_to_text(raw) if c.suffix == ".vtt" else raw

    out_root = str(Path("outputs") / video_id) if video_id else "outputs"
    caption = fetch_and_cache_vtt(video_id, output_dir=out_root, cache_only=True)
    if caption.get("success"):
        return caption.get("text", "") or ""
    return ""


def run_dr_direct(
    *,
    out_dir: str,
    video_id: Optional[str] = None,
    youtube_url: str = "",
    video_path: str = "",
    title: str = "",
    description: str = "",
    use_live_llm: bool = True,
    max_transcript_chars: Optional[int] = None,
    duration_sec: float = 0.0,
) -> Dict[str, Any]:
    """
    Run grounded Deep Research-style pass without a prior claims JSON.

    Bypasses DEEP_RESEARCH_MIN_CLAIMS by calling the Gemini client on a synthetic
    payload (empty claims_breakdown) rather than generate_deep_research_report.
    """
    from verityngn.services.ablation.cost import (
        build_arm_cost,
        estimate_transcript_tokens,
        write_arm_cost,
    )
    from verityngn.services.deepresearch.client import (
        DeepResearchConfigError,
        DeepResearchResult,
        run_deep_research,
    )
    from verityngn.services.deepresearch.renderer import (
        render_html_to_pdf,
        render_markdown_to_html,
    )

    t0 = time.perf_counter()
    os.makedirs(out_dir, exist_ok=True)

    vid = video_id or _extract_video_id_from_url(youtube_url) or ""
    if not vid and video_path:
        from verityngn.utils.upload_id import video_id_from_file_path

        vid = video_id_from_file_path(video_path)
    if not vid:
        raise ValueError("dr_direct requires video_id, youtube_url, or video_path")

    transcript = _try_load_transcript(vid, video_path)
    payload = build_direct_payload(
        video_id=vid,
        title=title,
        description=description,
        transcript=transcript,
        youtube_url=youtube_url,
        video_path=video_path,
        max_transcript_chars=max_transcript_chars,
    )
    fetched = int(payload.get("transcript_chars_fetched") or 0)
    used = int(payload.get("transcript_chars_used") or 0)
    truncated = bool(payload.get("transcript_truncated"))

    # Inject risk prompt into title so it appears in user prefix context
    payload["_system_risk_brief"] = _DIRECT_PROMPT

    sanitized_path = os.path.join(out_dir, f"{vid}_direct_sanitized_input.json")
    with open(sanitized_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Prepend risk instruction into the data blob the client serializes
    client_payload = {
        "instructions": _DIRECT_PROMPT,
        "video": {k: v for k, v in payload.items() if not k.startswith("_")},
    }

    n_llm_calls = 0
    output_tokens = 0
    if use_live_llm:
        try:
            result: DeepResearchResult = run_deep_research(client_payload)
            n_llm_calls = 1
            output_tokens = max(0, (result.output_bytes or 0) // 4)
        except DeepResearchConfigError as exc:
            logger.error("DR-direct config error: %s", exc)
            return {
                "status": "failed",
                "arm": "dr_direct",
                "reason": str(exc),
                "video_id": vid,
                "elapsed_sec": time.perf_counter() - t0,
                "sanitized_path": sanitized_path,
                "transcript_chars": fetched,
                "transcript_chars_fetched": fetched,
                "transcript_chars_used": used,
                "transcript_truncated": truncated,
            }
    else:
        stub_md = (
            f"# Direct risk brief (offline stub)\n\nVideo `{vid}`.\n\n"
            f"Transcript chars used: {used} (fetched {fetched}).\n\n"
            "[Reference: Currently Claim is Unverified]\n"
            + ("x" * 1100)
        )
        result = DeepResearchResult(
            markdown=stub_md,
            grounding_metadata="{}",
            model_id="offline-stub",
            prompt_version="dr_direct_stub",
            queries=[],
        )
        output_tokens = len(stub_md) // 4

    md_path = os.path.join(out_dir, f"{vid}_direct_risk_report.md")
    html_path = os.path.join(out_dir, f"{vid}_direct_risk_report.html")
    pdf_path = os.path.join(out_dir, f"{vid}_direct_risk_report.pdf")
    grounding_path = os.path.join(out_dir, f"{vid}_direct_risk_report.grounding.json")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(result.markdown)
    html = render_markdown_to_html(
        result.markdown, vid, title=title or f"Direct risk brief — {vid}"
    )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    pdf_ok = False
    try:
        import asyncio

        pdf_ok = bool(asyncio.run(render_html_to_pdf(html, pdf_path)))
    except Exception as exc:  # noqa: BLE001
        logger.warning("DR-direct PDF skipped: %s", exc)

    with open(grounding_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "arm": "dr_direct",
                "video_id": vid,
                "model_id": result.model_id,
                "prompt_version": result.prompt_version,
                "output_bytes": result.output_bytes,
                "search_queries": result.queries,
                "grounding_metadata": result.grounding_metadata,
            },
            f,
            indent=2,
        )

    elapsed = time.perf_counter() - t0
    input_tokens = estimate_transcript_tokens(used) + 800  # prompt overhead
    cost = build_arm_cost(
        arm="dr_direct",
        latency_sec=elapsed,
        n_llm_calls=n_llm_calls,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        transcript_chars_fetched=fetched,
        transcript_chars_used=used,
        duration_sec=duration_sec,
        truncated=truncated,
    )
    cost_path = write_arm_cost(out_dir, cost)

    return {
        "status": "completed",
        "arm": "dr_direct",
        "video_id": vid,
        "markdown_path": md_path,
        "html_path": html_path,
        "pdf_path": pdf_path if pdf_ok else None,
        "grounding_path": grounding_path,
        "sanitized_path": sanitized_path,
        "output_bytes": result.output_bytes,
        "model_id": result.model_id,
        "elapsed_sec": elapsed,
        "transcript_chars": used,
        "transcript_chars_fetched": fetched,
        "transcript_chars_used": used,
        "transcript_truncated": truncated,
        "n_claims_in_payload": 0,
        "n_llm_calls": n_llm_calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "usd_estimate": cost.get("usd_estimate"),
        "arm_cost_path": cost_path,
        "arm_cost": cost,
    }
