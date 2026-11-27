"""Video engine interface and the VerityNgn adapter (Gemini direct-URL path only).

The light tier wires two existing VerityNgn paths, neither of which downloads
the video: the Gemini YouTube-URL transcript (``caption_fetch``) and the Gemini
YouTube-URL claim extractor (``workflows.analysis``). The full tier (claim
verification with web evidence) runs on the hosted runs API and is reported
as not installed here rather than approximated.
"""

from __future__ import annotations

import asyncio
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Callable, Protocol

from verityngn.agent.mcp_v2.errors import EngineNotInstalled, ToolFailure


class VideoEngine(Protocol):
    name: str
    version: str

    def analyze(self, video_id: str, *, tier: str, domain_pack: str, progress: Callable[[str], None]) -> dict[str, Any]:
        """Return ``{"vtt": str, "claims": [{"claim_text", "start_s", "end_s"?, "claim_kind"?, "speaker"?}], "model": str}``."""
        ...


def parse_timestamp(value: Any) -> float | None:
    m = re.search(r"(?:(\d+):)?(\d{1,2}):(\d{2})", str(value or ""))
    if not m:
        return None
    h, mnt, s = m.groups()
    return int(h or 0) * 3600 + int(mnt) * 60 + int(s)


class VerityNgnVideoEngine:
    name = "verityngn"

    @property
    def version(self) -> str:
        try:
            from importlib.metadata import version

            return version("verityngn")
        except Exception:  # noqa: BLE001
            return ""

    def analyze(self, video_id: str, *, tier: str, domain_pack: str, progress: Callable[[str], None]) -> dict[str, Any]:
        if tier == "full":
            raise EngineNotInstalled(
                "verityngn-full",
                "The full tier (claim verification with web evidence) runs on the hosted runs API, not in this open-source adapter.",
                alternative="Run analyze_video with tier 'light' to extract time-anchored claims.",
            )
        try:
            from verityngn.services.video import caption_fetch
            from verityngn.workflows import analysis
        except ImportError as exc:
            raise EngineNotInstalled(
                "verityngn-video",
                f"The VerityNgn video stack is not installed on this server (missing {exc.name}).",
                alternative="Install verityngn with its Gemini and Vertex dependencies (pip install 'verityngn[deep]'), or upload a transcript with register_document.",
            ) from None
        if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("VERITY_GEMINI_KEY") or os.environ.get("GOOGLE_API_KEY")):
            raise ToolFailure(
                "UPSTREAM",
                "Video analysis is not configured on this server (no Gemini key).",
                alternative="Upload the transcript as text/vtt with register_document and assess it.",
            )
        url = f"https://www.youtube.com/watch?v={video_id}"
        progress("transcribing")
        with tempfile.TemporaryDirectory() as tmp:
            got = caption_fetch._fetch_via_gemini_youtube(video_id, url, tmp, 200_000)
            if not got.get("success") or not got.get("vtt_path"):
                raise ToolFailure("UPSTREAM", f"Transcript failed: {got.get('error') or 'unknown error'}")
            vtt = Path(got["vtt_path"]).read_text(encoding="utf-8")
        progress("extracting claims")
        extracted = asyncio.run(analysis.extract_claims_with_gemini_multimodal_youtube_url(url, video_id, {"duration": 0}))
        if extracted.get("error"):
            raise ToolFailure("UPSTREAM", str(extracted["error"]))
        claims = []
        for c in extracted.get("claims") or []:
            start = parse_timestamp(c.get("timestamp"))
            claims.append(
                {
                    "claim_text": str(c.get("claim_text") or "").strip(),
                    "start_s": start,
                    "claim_kind": c.get("claim_kind"),
                    "speaker": c.get("speaker"),
                }
            )
        return {"vtt": vtt, "claims": [c for c in claims if c["claim_text"]], "model": got.get("model", "")}
