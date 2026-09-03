"""
Pluggable transcript providers for reliable YouTube caption acquisition (T-TX-002).

Condition taxonomy (C0–C6):
  C0 Cached .en.vtt present
  C1 Owner/manual captions public
  C2 Auto (ASR) captions, cookies valid
  C3 PoToken/SABR block → paid vendor (Supadata)
  C4 No captions published → vendor generate or ASR
  C5 Age/region/members gated → ASR on obtainable audio, else fail
  C6 Non-English only → vendor with lang, else full multimodal
"""
from __future__ import annotations

from verityngn.services.video.transcript_providers.base import (
    TranscriptResult,
    cues_to_vtt,
)
from verityngn.services.video.transcript_providers.registry import (
    fetch_via_providers,
    provider_chain_from_env,
)

__all__ = [
    "TranscriptResult",
    "cues_to_vtt",
    "fetch_via_providers",
    "provider_chain_from_env",
]
