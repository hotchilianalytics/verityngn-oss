"""Unit tests for caption_fetch and tier router."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from verityngn.services.video.caption_fetch import (
    analysis_dir_for,
    canonical_vtt_path,
    discover_cookie_paths,
    fetch_and_cache_vtt,
    gemini_vtt_path,
    vtt_to_text,
)


SAMPLE_VTT = """WEBVTT

00:00:01.000 --> 00:00:03.000
Hello <c>world</c>

00:00:04.000 --> 00:00:06.000
Second line
"""


class TestVttParser:
    def test_vtt_to_text_strips_tags_and_timestamps(self):
        text = vtt_to_text(SAMPLE_VTT)
        assert "Hello world" in text
        assert "Second line" in text
        assert "[00:01]" in text or "[00:04]" in text

    def test_vtt_to_text_respects_max_chars(self):
        long_body = "word " * 20000
        vtt = f"WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n{long_body}"
        assert len(vtt_to_text(vtt, max_chars=100)) <= 104


class TestCaptionPaths:
    def test_analysis_dir_per_video_root(self, tmp_path):
        vid = "abc12345678"
        run = tmp_path / vid
        assert analysis_dir_for(str(run), vid) == run / "analysis"

    def test_canonical_vtt_path(self, tmp_path):
        vid = "abc12345678"
        run = tmp_path / vid
        assert canonical_vtt_path(str(run), vid) == run / "analysis" / f"{vid}.en.vtt"

    def test_gemini_vtt_path_never_en_vtt(self, tmp_path):
        vid = "abc12345678"
        run = tmp_path / vid
        assert gemini_vtt_path(str(run), vid).name == f"{vid}.gemini.vtt"


class TestCacheHit:
    def test_fetch_uses_cached_vtt(self, tmp_path):
        vid = "tLJC8hkK-ao"
        run = tmp_path / vid
        adir = run / "analysis"
        adir.mkdir(parents=True)
        vtt = adir / f"{vid}.en.vtt"
        vtt.write_text(SAMPLE_VTT, encoding="utf-8")

        with patch.dict(os.environ, {"SKIP_LIVE_CAPTION_FETCH": "1"}):
            result = fetch_and_cache_vtt(vid, output_dir=str(run), cache_only=True)

        assert result["success"] is True
        assert result["source"] == "cached_vtt"
        assert "Hello world" in result["text"]

    def test_cache_only_fails_without_file(self, tmp_path):
        vid = "nope1234567"
        run = tmp_path / vid
        run.mkdir()
        result = fetch_and_cache_vtt(vid, output_dir=str(run), cache_only=True)
        assert result["success"] is False
        assert result["source"] == "none"


class TestGeminiFallback:
    def test_gemini_fallback_writes_gemini_vtt_not_en_vtt(self, tmp_path):
        vid = "testvid1234"
        run = tmp_path / vid
        adir = run / "analysis"
        adir.mkdir(parents=True)
        en_vtt = adir / f"{vid}.en.vtt"
        gemini_vtt = adir / f"{vid}.gemini.vtt"

        fake_vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nGemini speech line\n"
        mock_response = type("R", (), {"text": fake_vtt})()

        with patch.dict(
            os.environ,
            {
                "SKIP_LIVE_CAPTION_FETCH": "0",
                "CAPTION_GEMINI_FALLBACK": "1",
                "VERITY_GEMINI_KEY": "test-key",
            },
        ):
            with patch(
                "verityngn.services.video.caption_fetch._fetch_via_cached_vtt",
                return_value={"success": False, "error": "miss"},
            ):
                with patch(
                    "verityngn.services.video.caption_fetch._fetch_via_ytdlp_subs",
                    return_value={"success": False, "error": "miss"},
                ):
                    with patch(
                        "verityngn.services.video.caption_fetch._fetch_via_youtube_transcript_api",
                        return_value={"success": False, "error": "miss"},
                    ):
                        with patch(
                            "verityngn.services.video.caption_fetch._fetch_via_gemini_youtube"
                        ) as mock_g:
                            mock_g.return_value = {
                                "success": True,
                                "text": "[00:01] Gemini speech line",
                                "vtt_path": str(gemini_vtt),
                                "source": "gemini_youtube",
                                "synthetic": True,
                            }
                            result = fetch_and_cache_vtt(
                                vid,
                                f"https://www.youtube.com/watch?v={vid}",
                                str(run),
                            )

        assert result["success"] is True
        assert result["source"] == "gemini_youtube"
        assert not en_vtt.is_file()
        assert result.get("synthetic") is True

    def test_gemini_disabled_when_skip_live(self, tmp_path):
        vid = "nope1234567"
        run = tmp_path / vid
        run.mkdir()
        with patch.dict(os.environ, {"SKIP_LIVE_CAPTION_FETCH": "1", "CAPTION_GEMINI_FALLBACK": "1"}):
            result = fetch_and_cache_vtt(vid, output_dir=str(run), cache_only=True)
        assert result["success"] is False
        assert "gemini" not in " ".join(result.get("errors") or [])


class TestTierRouter:
    def test_light_tier_calls_dr_direct(self, tmp_path):
        from verityngn.services.tiers.router import run_tier

        vid = "tLJC8hkK-ao"
        run = tmp_path / vid
        adir = run / "analysis"
        adir.mkdir(parents=True)
        (adir / f"{vid}.en.vtt").write_text(SAMPLE_VTT, encoding="utf-8")

        with patch("verityngn.services.ablation.direct.run_dr_direct") as mock_dr:
            mock_dr.return_value = {
                "status": "completed",
                "arm": "dr_direct",
                "markdown_path": str(run / f"{vid}_direct_risk_report.md"),
            }
            meta = run_tier(
                "light",
                youtube_url=f"https://www.youtube.com/watch?v={vid}",
                out_dir=str(tmp_path),
                use_live_llm=False,
            )
        assert meta["tier"] == "light"
        assert meta["status"] == "completed"
        mock_dr.assert_called_once()

    def test_unknown_tier_raises(self):
        from verityngn.services.tiers.router import run_tier

        with pytest.raises(ValueError, match="Unknown tier"):
            run_tier("bogus", youtube_url="https://youtube.com/watch?v=abc")  # type: ignore[arg-type]


@pytest.mark.live
def test_live_caption_fetch():
    """Requires fresh cookies.txt — skip in CI via -m 'not live'."""
    vid = os.getenv("VTT_TEST_VIDEO_ID", "tLJC8hkK-ao")
    url = f"https://www.youtube.com/watch?v={vid}"
    out = Path("outputs") / vid
    result = fetch_and_cache_vtt(vid, url, str(out))
    if not result.get("success"):
        pytest.skip(f"live caption fetch failed: {result.get('error')}")
    assert result.get("vtt_path")
    assert Path(result["vtt_path"]).is_file()
