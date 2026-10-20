"""Livestream restreams must not open unbounded Vertex segments."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from verityngn.config.video_segmentation import clamp_duration_seconds  # noqa: E402


def test_clamp_ces_livestream_window():
    ces_sec = 12 * 3600
    clamped, was_clamped = clamp_duration_seconds(ces_sec, limit_mins=90)
    assert was_clamped is True
    assert clamped == 90 * 60
    segments_if_500s = (clamped + 499) // 500
    assert segments_if_500s <= 12


def test_short_video_unchanged():
    dur, was_clamped = clamp_duration_seconds(1998, limit_mins=90)
    assert was_clamped is False
    assert dur == 1998


def test_zero_duration_passthrough():
    dur, was_clamped = clamp_duration_seconds(0, limit_mins=90)
    assert was_clamped is False
    assert dur == 0
