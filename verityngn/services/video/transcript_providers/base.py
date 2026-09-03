"""Shared transcript provider types."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class TranscriptCue:
    start_ms: int
    end_ms: int
    text: str


@dataclass
class TranscriptResult:
    success: bool
    text: str = ""
    cues: List[TranscriptCue] = field(default_factory=list)
    source: str = ""
    kind: str = ""  # vendor_native | vendor_generated | asr | ...
    latency_sec: float = 0.0
    usd_estimate: float = 0.0
    error: Optional[str] = None
    vtt: str = ""
    raw: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


class TranscriptProvider(Protocol):
    name: str

    def fetch(
        self,
        *,
        video_id: str,
        url: str = "",
        lang: str = "en",
        mode: str = "auto",
    ) -> TranscriptResult:
        ...


def cues_to_vtt(cues: List[TranscriptCue]) -> str:
    """Serialize cues to WEBVTT."""
    lines = ["WEBVTT", ""]
    for i, c in enumerate(cues, 1):
        lines.append(str(i))
        lines.append(f"{_ms_to_ts(c.start_ms)} --> {_ms_to_ts(c.end_ms)}")
        lines.append((c.text or "").strip())
        lines.append("")
    return "\n".join(lines)


def _ms_to_ts(ms: int) -> str:
    ms = max(0, int(ms))
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1000
    frac = ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d}.{frac:03d}"


def plain_text_to_cues(text: str, *, chunk_chars: int = 80) -> List[TranscriptCue]:
    """Best-effort cue split when vendor returns plain text only."""
    words = (text or "").split()
    if not words:
        return []
    cues: List[TranscriptCue] = []
    buf: List[str] = []
    t = 0
    for w in words:
        buf.append(w)
        if sum(len(x) + 1 for x in buf) >= chunk_chars:
            chunk = " ".join(buf)
            cues.append(TranscriptCue(start_ms=t, end_ms=t + 2000, text=chunk))
            t += 2000
            buf = []
    if buf:
        cues.append(TranscriptCue(start_ms=t, end_ms=t + 2000, text=" ".join(buf)))
    return cues
