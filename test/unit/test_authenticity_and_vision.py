"""Authenticity gate + AI detection + MediaPipe import smoke."""
from __future__ import annotations

from pathlib import Path

from verityngn.services.authenticity import run_authenticity_gate
from verityngn.services.authenticity.adapters import (
    C2PAAdapter,
    CorsoundAdapter,
    OpenVisualDeepfakeAdapter,
)
from verityngn.services.video.ai_detection import analyze_audio_for_ai_indicators
from verityngn.services.vision import MediaPipeAdapter, NOT_FOR_EMPLOYMENT


def test_authenticity_gate_noop_pass():
    r = run_authenticity_gate(video_id="demo")
    assert r.passed is True
    assert r.gated is False
    d = r.to_dict()
    assert d["pass"] is True


def test_authenticity_gate_fails_on_deepfake():
    r = run_authenticity_gate(
        video_id="demo",
        visual={"status": "deepfake", "score": 0.1},
    )
    assert r.passed is False
    assert r.gated is True


def test_adapters_stub_safe():
    assert CorsoundAdapter().analyze("/tmp/missing.wav")["status"] == "stub"
    assert OpenVisualDeepfakeAdapter().analyze("/tmp/missing.mp4")["status"] == "stub"
    assert C2PAAdapter().analyze("/tmp/missing.mp4")["status"] == "stub"


def test_ai_detection_missing_file():
    out = analyze_audio_for_ai_indicators("/no/such/file.wav")
    assert out["ai_score"] == 0.0
    assert out["indicators"] == []


def test_mediapipe_adapter_import():
    adapter = MediaPipeAdapter()
    assert adapter.name == "mediapipe"
    assert "Not for employment" in NOT_FOR_EMPLOYMENT
    # available() depends on optional dep — just must not raise
    assert isinstance(adapter.available(), bool)
