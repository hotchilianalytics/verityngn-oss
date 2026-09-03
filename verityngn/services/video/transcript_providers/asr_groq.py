"""Groq Whisper ASR fallback for caption-less / blocked videos (C4/C5)."""
from __future__ import annotations

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Optional

from verityngn.services.video.transcript_providers.base import (
    TranscriptResult,
    cues_to_vtt,
    plain_text_to_cues,
)

logger = logging.getLogger(__name__)

# ~$0.02–0.04 / audio hour (2026-09-02)
_USD_PER_HOUR = float(os.getenv("GROQ_ASR_USD_PER_HOUR", "0.04"))


class GroqAsrProvider:
    name = "asr_groq"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (
            api_key
            or os.getenv("GROQ_API_KEY", "").strip()
            or os.getenv("TRANSCRIPT_GROQ_KEY", "").strip()
        )
        self.model = os.getenv("GROQ_ASR_MODEL", "whisper-large-v3-turbo").strip()

    def available(self) -> bool:
        return bool(self.api_key)

    def fetch(
        self,
        *,
        video_id: str,
        url: str = "",
        lang: str = "en",
        mode: str = "auto",
    ) -> TranscriptResult:
        t0 = time.perf_counter()
        if not self.api_key:
            return TranscriptResult(
                success=False,
                source=self.name,
                kind="asr",
                error="GROQ_API_KEY not set",
                latency_sec=time.perf_counter() - t0,
            )
        watch = url or f"https://www.youtube.com/watch?v={video_id}"
        try:
            audio_path, duration_sec = self._download_audio(watch, video_id)
        except Exception as exc:  # noqa: BLE001
            return TranscriptResult(
                success=False,
                source=self.name,
                kind="asr",
                error=f"audio download failed: {exc}",
                latency_sec=time.perf_counter() - t0,
            )
        try:
            text = self._transcribe(audio_path, lang=lang)
        except Exception as exc:  # noqa: BLE001
            return TranscriptResult(
                success=False,
                source=self.name,
                kind="asr",
                error=f"groq asr failed: {exc}",
                latency_sec=time.perf_counter() - t0,
            )
        finally:
            try:
                Path(audio_path).unlink(missing_ok=True)
            except Exception:  # noqa: BLE001
                pass

        if not (text or "").strip():
            return TranscriptResult(
                success=False,
                source=self.name,
                kind="asr",
                error="empty ASR transcript",
                latency_sec=time.perf_counter() - t0,
            )
        cues = plain_text_to_cues(text)
        usd = (duration_sec / 3600.0) * _USD_PER_HOUR if duration_sec else _USD_PER_HOUR * 0.25
        return TranscriptResult(
            success=True,
            text=text,
            cues=cues,
            source=self.name,
            kind="asr",
            latency_sec=time.perf_counter() - t0,
            usd_estimate=usd,
            vtt=cues_to_vtt(cues),
        )

    def _download_audio(self, url: str, video_id: str) -> tuple[str, float]:
        import yt_dlp

        tmp = tempfile.mkdtemp(prefix="vn_asr_")
        outtmpl = str(Path(tmp) / f"{video_id}.%(ext)s")
        opts = {
            "quiet": True,
            "no_warnings": True,
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "128",
                }
            ],
        }
        cookie = os.getenv("YTDLP_COOKIES", "").strip()
        if cookie and Path(cookie).is_file():
            opts["cookiefile"] = cookie
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
        duration = float((info or {}).get("duration") or 0)
        # Find resulting mp3
        candidates = list(Path(tmp).glob(f"{video_id}.*"))
        if not candidates:
            raise FileNotFoundError(f"no audio written in {tmp}")
        # Prefer mp3
        mp3 = [p for p in candidates if p.suffix.lower() == ".mp3"]
        path = str(mp3[0] if mp3 else candidates[0])
        return path, duration

    def _transcribe(self, audio_path: str, *, lang: str = "en") -> str:
        # Prefer official groq SDK if present; else raw HTTP multipart
        try:
            from groq import Groq  # type: ignore

            client = Groq(api_key=self.api_key)
            with open(audio_path, "rb") as f:
                tr = client.audio.transcriptions.create(
                    file=f,
                    model=self.model,
                    language=lang or None,
                    response_format="text",
                )
            if isinstance(tr, str):
                return tr
            return str(getattr(tr, "text", None) or tr)
        except ImportError:
            pass

        import json
        import urllib.request

        boundary = "----VNGroqBoundary"
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        filename = Path(audio_path).name
        body = (
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode()
            + audio_bytes
            + (
                f"\r\n--{boundary}\r\n"
                f'Content-Disposition: form-data; name="model"\r\n\r\n{self.model}\r\n'
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="response_format"\r\n\r\ntext\r\n'
                f"--{boundary}--\r\n"
            ).encode()
        )
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=300) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw)
            return str(data.get("text") or raw)
        except json.JSONDecodeError:
            return raw
