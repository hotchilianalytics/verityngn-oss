"""Unit tests for transcript provider adapters (offline / no network)."""
from __future__ import annotations

from verityngn.services.video.transcript_providers.base import (
    TranscriptCue,
    cues_to_vtt,
    plain_text_to_cues,
)
from verityngn.services.video.transcript_providers.registry import provider_chain_from_env
from verityngn.services.video.transcript_providers.supadata import SupadataProvider


def test_cues_to_vtt():
    vtt = cues_to_vtt(
        [
            TranscriptCue(0, 1500, "Hello"),
            TranscriptCue(1500, 3000, "World"),
        ]
    )
    assert vtt.startswith("WEBVTT")
    assert "Hello" in vtt
    assert "00:00:01.500" in vtt


def test_plain_text_to_cues():
    cues = plain_text_to_cues("one two three four five six seven eight nine ten", chunk_chars=20)
    assert len(cues) >= 1
    assert "one" in cues[0].text


def test_supadata_missing_key():
    prov = SupadataProvider(api_key="")
    assert not prov.available()
    r = prov.fetch(video_id="AAAAAAAAAAA")
    assert r.success is False
    assert "SUPADATA_API_KEY" in (r.error or "")


def test_provider_chain_default():
    chain = provider_chain_from_env()
    assert "cached" in chain or "ytdlp" in chain or "supadata" in chain
