"""Unit tests for congruence renormalization, nuisance, event-time IC, synthetic CAR gate."""
from __future__ import annotations

import math
import pytest

from verityngn.services.fusion.crossmodal import score_crossmodal
from verityngn.services.quant.ic import event_time_ic, daily_rank_ic, ic_summary
from verityngn.services.quant.nuisance import residualize_rows
from verityngn.services.quant.signal_quality import fidelity_of_row, nuisance_leak, n_required, score_signal_quality
from verityngn.services.text_risk.extract import score_disclosure_risk
from verityngn.services.timeseries.event_study import _synthetic_car


def test_missing_face_does_not_fill_constant():
    rows = [
        {"t_sec": 0, "text_sentiment": 0.2, "exuberance": 0.4, "sympathetic_arousal": None, "disfluency_rate": 0.0}
        for _ in range(3)
    ]
    # vary exuberance so S01 isn't a flat line
    rows[1]["exuberance"] = 0.9
    rows[2]["exuberance"] = 0.1
    out = score_crossmodal(rows, player_id="t")
    for s in out["segments"]:
        assert s["voice_face_divergence"] is None
        assert s["face_text_divergence"] is None
        assert "face" in s["missing_channels"]
        assert "voice" in s["channels_used"]
    assert out["channels_policy"].startswith("renormalize")


def test_synthetic_car_refuses_without_flag():
    with pytest.raises(RuntimeError):
        _synthetic_car("PLTR", "2026-05-04", 1)
    v = _synthetic_car("PLTR", "2026-05-04", 1, allow_synthetic=True)
    assert -0.04 < v < 0.04


def test_event_time_ic_defined_on_staggered_dates():
    rows = [
        {"date": "2025-05-05", "prediction": 0.9, "y": 0.01, "event_date": "2025-05-05"},
        {"date": "2025-08-04", "prediction": 0.8, "y": -0.02, "event_date": "2025-08-04"},
        {"date": "2025-11-03", "prediction": 0.2, "y": 0.04, "event_date": "2025-11-03"},
        {"date": "2026-02-02", "prediction": 0.1, "y": 0.05, "event_date": "2026-02-02"},
    ]
    assert daily_rank_ic(rows) == []  # one name per date
    ic = event_time_ic(rows)
    assert ic == ic  # not NaN


def test_nuisance_residual_reduces_n_claims_leak():
    rows = []
    for i, n in enumerate([5, 6, 26, 36, 38, 38, 40]):
        rows.append({"s01": 0.74 + 0.004 * n, "n_claims": n, "duration_sec": 600, "n_segments": n, "days_to_print": 40})
    leak_raw = nuisance_leak(rows, factor_key="s01")
    resid = residualize_rows(rows, factor_key="s01")
    leak_res = nuisance_leak(resid, factor_key="s01_resid")
    assert leak_raw["max_abs"] > 0.5
    assert leak_res["max_abs"] < leak_raw["max_abs"]


def test_s15_dictionary_runs():
    hit = score_disclosure_risk("Climate emissions and AI foundation model regulation pose antitrust risk.", ticker="NVDA")
    miss = score_disclosure_risk("The cafeteria served pasta.", ticker="NVDA")
    assert hit["value"] > miss["value"]
    assert hit["id"].startswith("S15")


def test_fidelity_offline_is_low():
    f = fidelity_of_row({
        "live_gemini": False,
        "audio_source": "prosody_proxy",
        "gemini_source": "offline_proxy",
        "vision_source": "",
        "asr_source": "",
        "sympathetic_arousal": None,
    })
    assert f < 0.3


def test_fidelity_credits_measured_audio_asr_gemini():
    f = fidelity_of_row({
        "live_gemini": True,
        "audio_source": "audeering_wav2vec2",
        "gemini_source": "gemini",
        "vision_source": "",
        "asr_source": "faster_whisper",
        "sympathetic_arousal": None,
    })
    assert f == 0.6


def test_fidelity_credits_mediapipe_vision():
    f = fidelity_of_row({
        "live_gemini": True,
        "audio_source": "audeering_wav2vec2",
        "gemini_source": "gemini",
        "vision_source": "mediapipe_face_landmarker",
        "asr_source": "faster_whisper",
        "sympathetic_arousal": 0.55,
    })
    assert f == 1.0


def test_fidelity_rejects_unknown_vision_tag():
    f = fidelity_of_row({
        "live_gemini": False,
        "audio_source": "audeering_wav2vec2",
        "gemini_source": "",
        "vision_source": "hash_seeded_fake",
        "asr_source": "faster_whisper",
        "sympathetic_arousal": None,
    })
    # audio + asr only (2/5); unknown vision and missing arousal/gemini = 0
    assert abs(f - 0.4) < 1e-9


def test_face_channel_enters_s01_when_arousal_present():
    rows = [
        {
            "t_sec": 0,
            "text_sentiment": 0.2,
            "exuberance": 0.4,
            "sympathetic_arousal": 0.7,
            "disfluency_rate": 0.0,
        }
    ]
    out = score_crossmodal(rows, player_id="t")
    s = out["segments"][0]
    assert s["voice_face_divergence"] is not None
    assert s["face_text_divergence"] is not None
    assert "face" in s["channels_used"]
    assert "face" not in s["missing_channels"]
