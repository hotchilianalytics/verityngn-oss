"""Supadata hosted YouTube transcript API (paid volume path for C3/C4)."""
from __future__ import annotations

import logging
import os
import time
import urllib.parse
from typing import Any, Dict, List, Optional

from verityngn.services.video.transcript_providers.base import (
    TranscriptCue,
    TranscriptResult,
    cues_to_vtt,
    plain_text_to_cues,
)

logger = logging.getLogger(__name__)

_BASE = os.getenv("SUPADATA_API_BASE", "https://api.supadata.ai/v1").rstrip("/")
# Economics snapshot 2026-09-02: ~$0.99–$1.57 / 1k at Mega/Giga; generate = 2 credits/min
_USD_PER_NATIVE = float(os.getenv("SUPADATA_USD_PER_TRANSCRIPT", "0.00157"))
_USD_PER_GENERATE_MIN = float(os.getenv("SUPADATA_USD_PER_GENERATE_MIN", "0.00314"))


class SupadataProvider:
    name = "supadata"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (
            api_key
            or os.getenv("SUPADATA_API_KEY", "").strip()
            or os.getenv("TRANSCRIPT_SUPADATA_KEY", "").strip()
        )

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
                kind="vendor_native",
                error="SUPADATA_API_KEY not set",
                latency_sec=time.perf_counter() - t0,
            )
        watch = url or f"https://www.youtube.com/watch?v={video_id}"
        allow_generate = os.getenv("TRANSCRIPT_ALLOW_GENERATE", "").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        # Prefer native captions first unless explicitly generating
        modes = [mode]
        if mode == "auto" and not allow_generate:
            modes = ["native", "auto"] if allow_generate else ["native"]
        elif mode == "auto" and allow_generate:
            modes = ["auto"]

        last_err = "no attempt"
        for m in modes:
            if m == "generate" and not allow_generate:
                continue
            try:
                result = self._request(watch, lang=lang, mode=m)
                elapsed = time.perf_counter() - t0
                if result.get("success"):
                    kind = (
                        "vendor_generated"
                        if m == "generate" or result.get("generated")
                        else "vendor_native"
                    )
                    usd = _USD_PER_NATIVE
                    if kind == "vendor_generated":
                        # duration unknown here — flat estimate for generate
                        usd = max(_USD_PER_NATIVE, _USD_PER_GENERATE_MIN * 10)
                    cues = result.get("cues") or []
                    vtt = cues_to_vtt(cues) if cues else result.get("vtt") or ""
                    text = result.get("text") or ""
                    return TranscriptResult(
                        success=True,
                        text=text,
                        cues=cues,
                        source=self.name if m != "generate" else "supadata_generate",
                        kind=kind,
                        latency_sec=elapsed,
                        usd_estimate=usd,
                        vtt=vtt,
                        raw=result.get("raw"),
                    )
                last_err = str(result.get("error") or "unknown")
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
                logger.warning("Supadata mode=%s failed: %s", m, exc)
        return TranscriptResult(
            success=False,
            source=self.name,
            kind="vendor_native",
            error=last_err,
            latency_sec=time.perf_counter() - t0,
        )

    def _request(self, url: str, *, lang: str, mode: str) -> Dict[str, Any]:
        import urllib.request

        q = urllib.parse.urlencode(
            {
                "url": url,
                "lang": lang,
                "text": "false",
                "mode": mode,
            }
        )
        endpoint = f"{_BASE}/transcript?{q}"
        req = urllib.request.Request(
            endpoint,
            headers={
                "x-api-key": self.api_key,
                "Accept": "application/json",
                "User-Agent": "verityngn-oss/3.0.0",
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
            status = getattr(resp, "status", 200)
            body = resp.read().decode("utf-8", errors="replace")
            import json

            data = json.loads(body) if body else {}
            if status == 202 or data.get("jobId") or data.get("job_id"):
                job_id = data.get("jobId") or data.get("job_id")
                data = self._poll_job(job_id)
            return self._parse_payload(data, mode=mode)

    def _poll_job(self, job_id: str, *, max_wait_sec: float = 90.0) -> Dict[str, Any]:
        import json
        import urllib.request

        deadline = time.time() + max_wait_sec
        endpoint = f"{_BASE}/transcript/{job_id}"
        while time.time() < deadline:
            req = urllib.request.Request(
                endpoint,
                headers={
                    "x-api-key": self.api_key,
                    "Accept": "application/json",
                    "User-Agent": "verityngn-oss/3.0.0",
                },
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
                data = json.loads(resp.read().decode("utf-8", errors="replace") or "{}")
            status = str(data.get("status") or "").lower()
            if status in ("completed", "complete", "success", "done") or data.get("content") or data.get("transcript"):
                return data
            if status in ("failed", "error"):
                raise RuntimeError(f"Supadata job failed: {data}")
            time.sleep(2.0)
        raise TimeoutError(f"Supadata job {job_id} timed out after {max_wait_sec}s")

    def _parse_payload(self, data: Dict[str, Any], *, mode: str) -> Dict[str, Any]:
        content = data.get("content") or data.get("transcript") or data.get("text")
        chunks = data.get("chunks") or data.get("segments") or []
        cues: List[TranscriptCue] = []
        if isinstance(chunks, list) and chunks:
            for ch in chunks:
                if not isinstance(ch, dict):
                    continue
                text = str(ch.get("text") or "").strip()
                if not text:
                    continue
                offset = int(ch.get("offset") or ch.get("start") or ch.get("start_ms") or 0)
                # offset may be ms or seconds
                if offset < 10_000 and "start_ms" not in ch:
                    # ambiguous — treat small numbers as ms if duration also small
                    pass
                duration = int(ch.get("duration") or ch.get("dur") or 2000)
                if offset < 1000 and duration < 100 and "offset" in ch:
                    # likely seconds → ms
                    offset = int(float(ch["offset"]) * 1000)
                    duration = int(float(ch.get("duration") or 2) * 1000)
                cues.append(
                    TranscriptCue(start_ms=offset, end_ms=offset + max(duration, 1), text=text)
                )
        text = ""
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            text = " ".join(str(x.get("text") if isinstance(x, dict) else x) for x in content)
        if not text and cues:
            text = " ".join(c.text for c in cues)
        if text and not cues:
            cues = plain_text_to_cues(text)
        if not text:
            err = data.get("message") or data.get("error") or data.get("details")
            if isinstance(err, dict):
                err = err.get("message") or str(err)
            return {
                "success": False,
                "error": f"empty Supadata payload: {err or list(data.keys())}",
                "raw": {k: data[k] for k in list(data)[:20]},
            }
        return {
            "success": True,
            "text": text,
            "cues": cues,
            "generated": mode == "generate" or bool(data.get("generated")),
            "raw": {k: data[k] for k in list(data)[:20]},
        }
