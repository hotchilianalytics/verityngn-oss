"""Transcript-only claim extraction arm for modality ablation."""
from __future__ import annotations

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
        "context": "Speaker asserts clinical testing.",
    },
    {
        "claim_text": "Harvard researchers validated the formula.",
        "timestamp": "01:12",
        "source_type": "spoken",
        "context": "Authority attribution in speech.",
    },
    {
        "claim_text": "Customers lose weight in two weeks without diet changes.",
        "timestamp": "02:05",
        "source_type": "spoken",
        "context": "Efficacy claim spoken by host.",
    },
]

_EXTRACT_PROMPT = """You extract factual claims from a YouTube video TRANSCRIPT only.

Rules:
1. Use ONLY spoken/caption text in the transcript. Do NOT invent visual overlays,
   on-screen charts, logos, or graphics that are not stated in the transcript.
2. Every claim must set source_type to "spoken".
3. Prefer concrete, verifiable assertions over opinions.
4. Include approximate timestamps when the transcript provides them; otherwise use "unknown".
5. Return ONLY valid JSON (no markdown fences):

{{
  "claims": [
    {{
      "claim_text": "Exact factual claim",
      "timestamp": "MM:SS or unknown",
      "source_type": "spoken",
      "context": "Short supporting quote from transcript"
    }}
  ]
}}

Video title: {title}
Video id: {video_id}

Transcript:
{transcript}
"""


def _extract_video_id(url: str) -> Optional[str]:
    from verityngn.services.video.caption_fetch import extract_video_id

    return extract_video_id(url)


def fetch_youtube_transcript(video_id: str, max_chars: int = 50000) -> Dict[str, Any]:
    """Fetch English captions via shared caption_fetch module."""
    from verityngn.services.video.caption_fetch import fetch_youtube_transcript as _fetch

    return _fetch(video_id, max_chars=max_chars)


def _parse_claims_json(raw: str) -> List[Dict[str, Any]]:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    data = json.loads(text)
    claims = data.get("claims") if isinstance(data, dict) else data
    if not isinstance(claims, list):
        return []
    out: List[Dict[str, Any]] = []
    for c in claims:
        if isinstance(c, dict):
            item = dict(c)
            item["source_type"] = "spoken"
            item.setdefault("claim_text", str(c.get("text") or ""))
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


def extract_claims_from_transcript(
    transcript: str,
    *,
    video_id: str = "",
    title: str = "",
    use_live_llm: bool = True,
) -> List[Dict[str, Any]]:
    """Text-only LLM claim extract; offline returns fixture."""
    if not use_live_llm:
        return [dict(c) for c in _OFFLINE_FIXTURE]

    if not (transcript or "").strip():
        return []

    prompt = _EXTRACT_PROMPT.format(
        title=title or f"Video {video_id}",
        video_id=video_id,
        transcript=transcript[:45000],
    )

    # Prefer Gemini Developer API (VERITY_GEMINI_KEY) — same credential as Deep Research.
    # Vertex ChatVertexAI can 404 on some agent model IDs in local OSS envs.
    try:
        from google import genai
        from verityngn.config.settings import (
            AGENT_MODEL_NAME,
            DEEP_RESEARCH_API_KEY,
            DEEP_RESEARCH_MODEL,
        )

        if DEEP_RESEARCH_API_KEY:
            client = genai.Client(api_key=DEEP_RESEARCH_API_KEY)
            # Prefer ablation override, then DR model (commercial), then current Gemini flash.
            candidates = [
                os.getenv("ABLATION_CLAIM_MODEL"),
                DEEP_RESEARCH_MODEL,
                "gemini-3.6-flash",
                "gemini-3-flash-preview",
                AGENT_MODEL_NAME,
                "gemini-2.5-flash",
            ]
            last_err: Exception | None = None
            content = None
            for model in candidates:
                if not model:
                    continue
                try:
                    response = client.models.generate_content(
                        model=model, contents=prompt
                    )
                    content = getattr(response, "text", None) or str(response)
                    logger.info("Transcript claims via genai model=%s", model)
                    break
                except Exception as exc:  # noqa: BLE001
                    last_err = exc
                    logger.warning("genai model %s failed: %s", model, exc)
            if content is None:
                raise last_err or RuntimeError("no genai model succeeded")
            return _parse_claims_json(str(content))
    except Exception as exc:  # noqa: BLE001
        logger.warning("genai transcript extract failed, trying Vertex: %s", exc)

    try:
        from langchain_google_vertexai import ChatVertexAI
        from langchain_core.prompts import ChatPromptTemplate
        from verityngn.config.settings import AGENT_MODEL_NAME, PROJECT_ID, VERTEX_LOCATION

        chat_prompt = ChatPromptTemplate.from_template(_EXTRACT_PROMPT)
        llm = ChatVertexAI(
            model_name=AGENT_MODEL_NAME,
            temperature=0.1,
            max_output_tokens=4096,
            project=PROJECT_ID,
            location=VERTEX_LOCATION,
        )
        messages = chat_prompt.format_messages(
            title=title or f"Video {video_id}",
            video_id=video_id,
            transcript=transcript[:45000],
        )
        response = llm.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)
        if isinstance(content, list):
            content = "".join(
                (p.get("text") if isinstance(p, dict) else str(p)) for p in content
            )
        return _parse_claims_json(str(content))
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to extract transcript claims: %s", exc)
        return []


def run_transcript_claims_arm(
    *,
    out_dir: str,
    video_id: str = "",
    youtube_url: str = "",
    title: str = "",
    use_live_llm: bool = True,
) -> Dict[str, Any]:
    """Fetch captions, extract spoken claims, write claims_transcript.json."""
    t0 = time.perf_counter()
    os.makedirs(out_dir, exist_ok=True)
    vid = video_id or _extract_video_id(youtube_url) or "unknown"

    if use_live_llm and vid != "unknown":
        fetched = fetch_youtube_transcript(vid)
    else:
        fetched = {
            "success": True,
            "text": "[offline stub transcript] clinical trial Harvard weight loss",
            "error": None,
            "n_segments": 0,
        }

    transcript = fetched.get("text") or ""
    claims = extract_claims_from_transcript(
        transcript,
        video_id=vid,
        title=title,
        use_live_llm=use_live_llm,
    )

    inventory = {
        "arm": "transcript",
        "video_id": vid,
        "youtube_url": youtube_url,
        "title": title,
        "transcript_chars": len(transcript),
        "transcript_fetch_ok": bool(fetched.get("success")),
        "transcript_error": fetched.get("error"),
        "transcript_source": fetched.get("source"),
        "transcript_path": fetched.get("path"),
        "n_claims": len(claims),
        "claims": claims,
        "offline": not use_live_llm,
    }
    claims_path = Path(out_dir) / "claims_transcript.json"
    claims_path.write_text(json.dumps(inventory, indent=2, default=str), encoding="utf-8")

    md_lines = [
        f"# Transcript-only claim inventory — {vid}",
        "",
        f"Claims: **{len(claims)}** | Transcript chars: {len(transcript)}",
        "",
    ]
    for i, c in enumerate(claims, 1):
        md_lines.append(
            f"{i}. [{c.get('timestamp', '?')}] {c.get('claim_text', '')} "
            f"(source_type={c.get('source_type', 'spoken')})"
        )
    md_path = Path(out_dir) / "claims_transcript.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    return {
        "status": "completed",
        "arm": "transcript",
        "video_id": vid,
        "out_dir": out_dir,
        "claims_path": str(claims_path),
        "markdown_path": str(md_path),
        "n_claims": len(claims),
        "claims": claims,
        "transcript_chars": len(transcript),
        "transcript_source": fetched.get("source"),
        "elapsed_sec": time.perf_counter() - t0,
        "offline": not use_live_llm,
    }
