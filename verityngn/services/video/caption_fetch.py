"""Unified YouTube caption fetch — cached VTT → yt-dlp → transcript API → Gemini YouTube URL."""
from __future__ import annotations

import logging
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_VTT_TAG_RE = re.compile(r"<[^>]+>")
_VIDEO_ID_RE = re.compile(r"(?:v=|/shorts/|youtu\.be/)([A-Za-z0-9_-]{11})")

_VTT_GLOB_PATTERNS = (
    "{video_id}.en.vtt",
    "{video_id}.en-orig.vtt",
    "{video_id}.vtt",
    "{video_id}.en.srv3.vtt",
)

_GEMINI_VTT_SUFFIX = ".gemini.vtt"
_VENDOR_VTT_SUFFIX = ".vendor.vtt"

_GEMINI_TRANSCRIPT_PROMPT = """Transcribe the spoken English audio from this YouTube video.

Return ONLY valid WEBVTT format:
WEBVTT

00:00:01.000 --> 00:00:04.000
Spoken text here

Rules:
- Speech/captions only — no visual descriptions or on-screen text unless spoken aloud.
- Use HH:MM:SS.mmm timestamps.
- No markdown fences or commentary outside WEBVTT."""


def extract_video_id(url: str) -> Optional[str]:
    if not url:
        return None
    m = _VIDEO_ID_RE.search(url)
    return m.group(1) if m else None


def vtt_to_text(vtt: str, max_chars: int = 50000) -> str:
    """Strip WEBVTT chrome into timestamped plain text."""
    parts: List[str] = []
    cur_ts = ""
    for line in (vtt or "").splitlines():
        line = line.strip()
        if not line or line.upper().startswith("WEBVTT") or line.isdigit():
            continue
        if "-->" in line:
            start = line.split("-->", 1)[0].strip()
            start = start.split(".")[0]
            bits = start.split(":")
            if len(bits) == 3:
                cur_ts = f"{int(bits[0]) * 60 + int(bits[1]):02d}:{int(bits[2]):02d}"
            elif len(bits) == 2:
                cur_ts = f"{int(bits[0]):02d}:{int(bits[1]):02d}"
            else:
                cur_ts = start
            continue
        text = _VTT_TAG_RE.sub("", line).strip()
        if not text:
            continue
        parts.append(f"[{cur_ts}] {text}" if cur_ts else text)
    full = " ".join(parts)
    if len(full) > max_chars:
        full = full[:max_chars] + "..."
    return full


def analysis_dir_for(output_dir: str, video_id: str) -> Path:
    """Canonical analysis directory: ``{run_root}/analysis`` when run_root is per-video."""
    root = Path(output_dir)
    if root.name == video_id:
        return root / "analysis"
    nested = root / video_id / "analysis"
    if nested.is_dir() or not (root / "analysis").is_dir():
        return nested
    return root / "analysis"


def canonical_vtt_path(output_dir: str, video_id: str) -> Path:
    return analysis_dir_for(output_dir, video_id) / f"{video_id}.en.vtt"


def gemini_vtt_path(output_dir: str, video_id: str) -> Path:
    """Synthetic transcript cache — never overwrite a real ``.en.vtt``."""
    return analysis_dir_for(output_dir, video_id) / f"{video_id}{_GEMINI_VTT_SUFFIX}"


def _gemini_fallback_enabled() -> bool:
    if os.getenv("SKIP_LIVE_CAPTION_FETCH", "").strip().lower() in ("1", "true", "yes"):
        return False
    val = os.getenv("CAPTION_GEMINI_FALLBACK", "1").strip().lower()
    return val not in ("0", "false", "no", "off")


def discover_cookie_paths() -> List[Path]:
    """Cookie file discovery: YTDLP_COOKIES env, repo root, ui/cookies.txt."""
    out: List[Path] = []
    env_cookie = os.getenv("YTDLP_COOKIES", "").strip()
    if env_cookie:
        p = Path(env_cookie).expanduser()
        if p.is_file():
            out.append(p.resolve())

    roots = [Path.cwd()]
    try:
        pkg_root = Path(__file__).resolve().parents[3]
        if pkg_root not in roots:
            roots.append(pkg_root)
    except IndexError:
        pass

    for root in roots:
        for name in ("cookies.txt", "ui/cookies.txt"):
            p = (root / name).resolve()
            if p.is_file() and p not in out:
                out.append(p)

    for extra in (
        Path.home() / ".config" / "yt-dlp" / "cookies.txt",
        Path.home() / "cookies.txt",
    ):
        if extra.is_file() and extra.resolve() not in out:
            out.append(extra.resolve())
    return out


def _cached_vtt_candidates(video_id: str, output_dir: str = "") -> List[Path]:
    bases: List[Path] = []
    if output_dir:
        bases.append(analysis_dir_for(output_dir, video_id))
    bases.extend(
        [
            Path.cwd() / "outputs" / video_id / "analysis",
            Path.cwd() / "outputs" / video_id,
            Path.cwd() / "analysis",
            Path.cwd() / "downloads",
        ]
    )
    out: List[Path] = []
    seen: set[str] = set()
    gemini_name = f"{video_id}{_GEMINI_VTT_SUFFIX}"
    vendor_name = f"{video_id}{_VENDOR_VTT_SUFFIX}"
    for base in bases:
        for name in _VTT_GLOB_PATTERNS:
            p = base / name.format(video_id=video_id)
            key = str(p)
            if p.is_file() and key not in seen:
                seen.add(key)
                out.append(p)
        for extra_name in (vendor_name, gemini_name):
            gp = base / extra_name
            key = str(gp)
            if gp.is_file() and key not in seen:
                seen.add(key)
                out.append(gp)
    return out


def _fetch_via_cached_vtt(
    video_id: str, max_chars: int, output_dir: str = ""
) -> Dict[str, Any]:
    for path in _cached_vtt_candidates(video_id, output_dir):
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
            text = vtt_to_text(raw, max_chars)
            if text.strip():
                src = (
                    "cached_gemini_vtt"
                    if path.name.endswith(_GEMINI_VTT_SUFFIX)
                    else "cached_vendor_vtt"
                    if path.name.endswith(_VENDOR_VTT_SUFFIX)
                    else "cached_vtt"
                )
                logger.info("Using cached VTT: %s (%s chars)", path, len(text))
                return {
                    "success": True,
                    "text": text,
                    "vtt_path": str(path),
                    "error": None,
                    "source": src,
                }
        except OSError as exc:
            logger.debug("cached vtt read failed %s: %s", path, exc)
    return {
        "success": False,
        "text": "",
        "vtt_path": None,
        "error": "no usable cached .vtt found",
        "source": "cached_vtt",
    }


def _player_client() -> str:
    return os.getenv("CAPTION_PLAYER_CLIENT", "android").strip() or "android"


def _fetch_via_ytdlp_subs(
    video_id: str,
    url: str,
    output_dir: str,
    max_chars: int,
) -> Dict[str, Any]:
    import tempfile

    try:
        import yt_dlp
    except ImportError:
        return {
            "success": False,
            "text": "",
            "vtt_path": None,
            "error": "yt-dlp not installed",
            "source": "yt-dlp",
        }

    watch_url = url or f"https://www.youtube.com/watch?v={video_id}"
    cookies = discover_cookie_paths()
    cookiefile = str(cookies[0]) if cookies else None
    analysis_dir = analysis_dir_for(output_dir, video_id)
    analysis_dir.mkdir(parents=True, exist_ok=True)
    target_vtt = canonical_vtt_path(output_dir, video_id)
    errors: List[str] = []

    with tempfile.TemporaryDirectory(prefix="verity_subs_") as tmp:
        outtmpl = str(Path(tmp) / f"{video_id}.%(ext)s")
        ydl_opts: Dict[str, Any] = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "subtitlesformat": "vtt",
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "retries": 2,
            "socket_timeout": 30,
            "extractor_args": {"youtube": {"player_client": [_player_client()]}},
        }
        if cookiefile:
            ydl_opts["cookiefile"] = cookiefile
            logger.info("yt-dlp subs using cookies: %s", cookiefile)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([watch_url])
        except Exception as exc:  # noqa: BLE001
            errors.append(f"download: {exc}")

        vtts = sorted(Path(tmp).glob("*.vtt"))
        if not vtts:
            return {
                "success": False,
                "text": "",
                "vtt_path": None,
                "error": "; ".join(errors) or "yt-dlp wrote no .vtt",
                "source": "yt-dlp",
                "cookiefile": cookiefile,
            }

        raw_vtt = vtts[0].read_text(encoding="utf-8", errors="ignore")
        shutil.copy2(vtts[0], target_vtt)
        text = vtt_to_text(raw_vtt, max_chars)
        if not text.strip():
            return {
                "success": False,
                "text": "",
                "vtt_path": None,
                "error": f"empty vtt from {vtts[0].name}",
                "source": "yt-dlp",
            }
        return {
            "success": True,
            "text": text,
            "vtt_path": str(target_vtt),
            "error": None,
            "source": "yt-dlp",
            "cookiefile": cookiefile,
        }


def _fetch_via_youtube_transcript_api(video_id: str, max_chars: int) -> Dict[str, Any]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return {
            "success": False,
            "text": "",
            "vtt_path": None,
            "error": "youtube_transcript_api not installed",
            "source": "youtube_transcript_api",
        }

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None
        try:
            transcript = transcript_list.find_transcript(["en"]).fetch()
        except Exception:
            try:
                transcript = transcript_list.find_generated_transcript(["en"]).fetch()
            except Exception:
                for t in transcript_list:
                    transcript = t.fetch()
                    break

        if not transcript:
            return {
                "success": False,
                "text": "",
                "vtt_path": None,
                "error": "No transcript available",
                "source": "youtube_transcript_api",
            }

        parts: List[str] = []
        for entry in transcript:
            if isinstance(entry, dict):
                text = entry.get("text") or ""
                start = entry.get("start")
            else:
                text = getattr(entry, "text", "") or ""
                start = getattr(entry, "start", None)
            if start is not None:
                mins = int(float(start) // 60)
                secs = int(float(start) % 60)
                parts.append(f"[{mins:02d}:{secs:02d}] {text}")
            else:
                parts.append(text)

        full = " ".join(parts)
        if len(full) > max_chars:
            full = full[:max_chars] + "..."
        return {
            "success": True,
            "text": full,
            "vtt_path": None,
            "error": None,
            "n_segments": len(transcript),
            "source": "youtube_transcript_api",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "text": "",
            "vtt_path": None,
            "error": str(exc),
            "source": "youtube_transcript_api",
        }


def _fetch_via_gemini_youtube(
    video_id: str,
    url: str,
    output_dir: str,
    max_chars: int,
) -> Dict[str, Any]:
    """
    Synthesize a timestamped transcript via Gemini YouTube URL ingestion.

    Writes ``{video_id}.gemini.vtt`` — not YouTube's official caption file.
    """
    if not _gemini_fallback_enabled():
        return {
            "success": False,
            "text": "",
            "vtt_path": None,
            "error": "CAPTION_GEMINI_FALLBACK disabled",
            "source": "gemini_youtube",
        }

    from verityngn.config.settings import DEEP_RESEARCH_API_KEY, VIDEO_LENGTH_LIMIT_MINS

    api_key = (DEEP_RESEARCH_API_KEY or "").strip()
    if not api_key:
        return {
            "success": False,
            "text": "",
            "vtt_path": None,
            "error": "no Gemini API key (VERITY_GEMINI_KEY / GEMINI_API_KEY)",
            "source": "gemini_youtube",
        }

    watch_url = url or f"https://www.youtube.com/watch?v={video_id}"
    analysis_dir = analysis_dir_for(output_dir, video_id)
    analysis_dir.mkdir(parents=True, exist_ok=True)
    target = gemini_vtt_path(output_dir, video_id)
    # Never clobber a real YouTube caption file.
    if canonical_vtt_path(output_dir, video_id).is_file():
        logger.info("Skipping Gemini write — official .en.vtt already present")

    try:
        from google import genai
        from google.genai.types import FileData, HttpOptions, Part, VideoMetadata

        client = genai.Client(
            api_key=api_key,
            http_options=HttpOptions(api_version="v1"),
        )
        limit_seconds = max(60, VIDEO_LENGTH_LIMIT_MINS * 60)
        model = os.getenv("CAPTION_GEMINI_MODEL", "gemini-2.5-flash").strip()
        video_part = Part(
            file_data=FileData(file_uri=watch_url, mime_type="video/youtube"),
            video_metadata=VideoMetadata(end_offset=f"{limit_seconds}s"),
        )
        response = client.models.generate_content(
            model=model,
            contents=[video_part, _GEMINI_TRANSCRIPT_PROMPT],
        )
        raw = (getattr(response, "text", None) or str(response)).strip()
        if not raw:
            return {
                "success": False,
                "text": "",
                "vtt_path": None,
                "error": "empty Gemini transcript response",
                "source": "gemini_youtube",
            }
        if not raw.upper().startswith("WEBVTT"):
            raw = "WEBVTT\n\n" + raw
        if not target.is_file() or target.name.endswith(_GEMINI_VTT_SUFFIX):
            target.write_text(raw, encoding="utf-8")
        text = vtt_to_text(raw, max_chars)
        if not text.strip():
            return {
                "success": False,
                "text": "",
                "vtt_path": None,
                "error": "Gemini VTT parsed to empty text",
                "source": "gemini_youtube",
            }
        logger.info(
            "Gemini YouTube transcript fallback: %s (%s chars, model=%s)",
            target,
            len(text),
            model,
        )
        return {
            "success": True,
            "text": text,
            "vtt_path": str(target),
            "error": None,
            "source": "gemini_youtube",
            "model": model,
            "synthetic": True,
        }
    except ImportError:
        return {
            "success": False,
            "text": "",
            "vtt_path": None,
            "error": "google-genai not installed (pip install verityngn[deep])",
            "source": "gemini_youtube",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini YouTube caption fallback failed: %s", exc)
        return {
            "success": False,
            "text": "",
            "vtt_path": None,
            "error": str(exc),
            "source": "gemini_youtube",
        }


def fetch_and_cache_vtt(
    video_id: str,
    url: str = "",
    output_dir: str = "",
    *,
    max_chars: int = 50000,
    cache_only: bool | None = None,
) -> Dict[str, Any]:
    """
    Fetch English captions with commercial-parity fallbacks.

    Order: cached ``.en.vtt`` / ``.vendor.vtt`` / ``.gemini.vtt`` → yt-dlp
    (android + cookies) → youtube_transcript_api → paid providers (Supadata / Groq ASR)
    → Gemini YouTube URL (writes ``.gemini.vtt`` only).
    On yt-dlp success, writes through to ``{output_dir}/analysis/{video_id}.en.vtt``.
    """
    errors: List[str] = []
    if cache_only is None:
        cache_only = os.getenv("SKIP_LIVE_CAPTION_FETCH", "").strip() in ("1", "true", "yes")

    cached = _fetch_via_cached_vtt(video_id, max_chars, output_dir)
    if cached.get("success"):
        return {
            "success": True,
            "vtt_path": cached.get("vtt_path"),
            "text": cached.get("text", ""),
            "source": cached.get("source"),
            "errors": errors,
        }
    errors.append(f"cached: {cached.get('error')}")

    if cache_only:
        return {
            "success": False,
            "vtt_path": None,
            "text": "",
            "source": "none",
            "errors": errors,
            "error": " | ".join(errors),
        }

    ytdlp = _fetch_via_ytdlp_subs(video_id, url, output_dir, max_chars)
    if ytdlp.get("success"):
        return {
            "success": True,
            "vtt_path": ytdlp.get("vtt_path"),
            "text": ytdlp.get("text", ""),
            "source": ytdlp.get("source"),
            "errors": errors,
        }
    errors.append(f"yt-dlp: {ytdlp.get('error')}")

    api = _fetch_via_youtube_transcript_api(video_id, max_chars)
    if api.get("success"):
        return {
            "success": True,
            "vtt_path": api.get("vtt_path"),
            "text": api.get("text", ""),
            "source": api.get("source"),
            "errors": errors,
        }
    errors.append(f"api: {api.get('error')}")

    # Paid third-party path (Supadata / Groq ASR) — opt-in via keys + TRANSCRIPT_PROVIDERS
    try:
        from verityngn.services.video.transcript_providers import fetch_via_providers

        paid = fetch_via_providers(video_id, url or "", output_dir=output_dir)
        if paid.get("success"):
            text = paid.get("text") or ""
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            return {
                "success": True,
                "vtt_path": paid.get("vtt_path"),
                "text": text,
                "source": paid.get("source"),
                "kind": paid.get("kind"),
                "usd_estimate": paid.get("usd_estimate"),
                "attempts": paid.get("attempts"),
                "errors": errors,
            }
        errors.append(f"paid: {paid.get('error')}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"paid: {exc}")
        logger.warning("Paid transcript providers failed: %s", exc)

    gemini = _fetch_via_gemini_youtube(video_id, url, output_dir, max_chars)
    if gemini.get("success"):
        return {
            "success": True,
            "vtt_path": gemini.get("vtt_path"),
            "text": gemini.get("text", ""),
            "source": gemini.get("source"),
            "errors": errors,
            "synthetic": True,
            "model": gemini.get("model"),
        }
    errors.append(f"gemini: {gemini.get('error')}")

    logger.warning("All caption sources failed for %s: %s", video_id, " | ".join(errors))
    return {
        "success": False,
        "vtt_path": None,
        "text": "",
        "source": "none",
        "errors": errors,
        "error": " | ".join(errors),
    }


def fetch_youtube_transcript(video_id: str, max_chars: int = 50000) -> Dict[str, Any]:
    """Backward-compatible alias used by ablation transcript arm."""
    result = fetch_and_cache_vtt(video_id, output_dir=str(Path.cwd() / "outputs" / video_id))
    return {
        "success": result.get("success", False),
        "text": result.get("text", ""),
        "error": result.get("error") or (
            " | ".join(result.get("errors") or []) if not result.get("success") else None
        ),
        "source": result.get("source"),
        "path": result.get("vtt_path"),
    }
