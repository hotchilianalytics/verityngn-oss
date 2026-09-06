"""Agentic video understanding spike (VN_AGENTIC_VIDEO).

Uses GenerateContent with mediaProcessing=AGENTIC via REST so older
google-genai SDKs (without Part.media_processing) still work.
Falls back to caller on any failure.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def agentic_video_enabled() -> bool:
    return os.getenv("VN_AGENTIC_VIDEO", "0").lower() in ("1", "true", "t", "yes")


def _api_key() -> str:
    return (
        os.getenv("VERITY_GEMINI_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_AI_STUDIO_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or ""
    ).strip()


def _model_id() -> str:
    return (
        os.getenv("VN_VIDEO_MODEL")
        or os.getenv("DEEP_RESEARCH_MODEL")
        or "gemini-3.8-flash"
    ).strip()


def _thinking_level(duration_sec: float) -> str:
    # HIGH for long / dense chart-heavy videos
    if duration_sec and duration_sec > 3600:
        return "HIGH"
    return "MEDIUM"


def upload_file_for_gemini(local_path: str, api_key: str) -> Optional[str]:
    """Upload local mp4 via Files API; return file.uri or None."""
    try:
        import requests
    except ImportError:
        logger.warning("agentic_video: requests missing")
        return None

    path = Path(local_path)
    if not path.is_file():
        return None
    mime = "video/mp4"
    size = path.stat().st_size
    # Resumable upload (Gemini Files API)
    start = requests.post(
        "https://generativelanguage.googleapis.com/upload/v1beta/files"
        f"?key={api_key}",
        headers={
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(size),
            "X-Goog-Upload-Header-Content-Type": mime,
            "Content-Type": "application/json",
        },
        json={"file": {"display_name": path.name}},
        timeout=60,
    )
    start.raise_for_status()
    upload_url = start.headers.get("X-Goog-Upload-URL") or start.headers.get(
        "x-goog-upload-url"
    )
    if not upload_url:
        logger.warning("agentic_video: no upload URL in Files API start response")
        return None
    with open(path, "rb") as f:
        data = f.read()
    fin = requests.post(
        upload_url,
        headers={
            "Content-Length": str(size),
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize",
        },
        data=data,
        timeout=600,
    )
    fin.raise_for_status()
    body = fin.json()
    file_info = body.get("file") or body
    uri = file_info.get("uri")
    # Wait until ACTIVE
    name = file_info.get("name")
    if name:
        for _ in range(60):
            st = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/{name}?key={api_key}",
                timeout=30,
            )
            if st.ok:
                state = (st.json().get("state") or "").upper()
                if state == "ACTIVE":
                    uri = st.json().get("uri") or uri
                    break
                if state == "FAILED":
                    logger.error("agentic_video: file processing FAILED")
                    return None
            time.sleep(2)
    return uri


def generate_agentic_claims(
    *,
    prompt_text: str,
    video_uri: Optional[str] = None,
    local_path: Optional[str] = None,
    youtube_url: Optional[str] = None,
    duration_sec: float = 0,
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Run one agentic GenerateContent call.

    Returns (response_text, meta). response_text is None on failure.
    """
    meta: Dict[str, Any] = {
        "agentic_video": True,
        "model": _model_id(),
        "media_processing": "AGENTIC",
    }
    if not agentic_video_enabled():
        meta["skipped"] = "flag_off"
        return None, meta

    api_key = _api_key()
    if not api_key:
        meta["error"] = "no_api_key"
        return None, meta

    try:
        import requests
    except ImportError as exc:
        meta["error"] = str(exc)
        return None, meta

    file_uri = video_uri
    mime = "video/mp4"
    if youtube_url and not file_uri:
        file_uri = youtube_url
        mime = "video/youtube"
    elif local_path and not file_uri:
        t0 = time.time()
        file_uri = upload_file_for_gemini(local_path, api_key)
        meta["upload_s"] = round(time.time() - t0, 2)
        if not file_uri:
            meta["error"] = "upload_failed"
            return None, meta

    if not file_uri:
        meta["error"] = "no_video_uri"
        return None, meta

    model = _model_id()
    thinking = _thinking_level(duration_sec)
    meta["thinking_level"] = thinking
    meta["file_uri"] = file_uri

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "fileData": {"fileUri": file_uri, "mimeType": mime},
                        "mediaProcessing": "AGENTIC",
                    },
                    {"text": prompt_text},
                ],
            }
        ],
        "generationConfig": {
            "thinkingConfig": {"thinkingLevel": thinking},
        },
    }

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    t0 = time.time()
    try:
        resp = requests.post(url, json=body, timeout=600)
        meta["http_status"] = resp.status_code
        meta["latency_s"] = round(time.time() - t0, 2)
        if not resp.ok:
            meta["error"] = resp.text[:500]
            logger.warning(
                "agentic_video: HTTP %s — %s", resp.status_code, resp.text[:200]
            )
            return None, meta
        data = resp.json()
        # usage metadata if present
        um = data.get("usageMetadata") or {}
        meta["usage"] = {
            "prompt_token_count": um.get("promptTokenCount"),
            "candidates_token_count": um.get("candidatesTokenCount"),
            "total_token_count": um.get("totalTokenCount"),
        }
        cands = data.get("candidates") or []
        texts: List[str] = []
        for c in cands:
            parts = ((c.get("content") or {}).get("parts")) or []
            for p in parts:
                if p.get("text"):
                    texts.append(p["text"])
        text = "\n".join(texts).strip()
        if not text:
            meta["error"] = "empty_response"
            return None, meta
        meta["status"] = "ok"
        meta["response_chars"] = len(text)
        return text, meta
    except Exception as exc:  # noqa: BLE001
        meta["error"] = str(exc)
        meta["latency_s"] = round(time.time() - t0, 2)
        logger.warning("agentic_video failed: %s", exc)
        return None, meta


def parse_claims_json(text: str) -> List[Dict[str, Any]]:
    """Best-effort extract claims list from model JSON."""
    if not text:
        return []
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].lstrip()
    try:
        data = json.loads(raw)
    except Exception:
        # find outermost JSON object/array
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(raw[start : end + 1])
            except Exception:
                return []
        else:
            return []
    if isinstance(data, list):
        return [c for c in data if isinstance(c, dict)]
    if isinstance(data, dict):
        claims = data.get("claims") or data.get("claims_breakdown") or []
        return [c for c in claims if isinstance(c, dict)]
    return []
