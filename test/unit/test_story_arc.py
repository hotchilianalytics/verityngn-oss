"""Vision story_arc continuity stub smoke."""
from verityngn.services.vision.story_arc import summarize_continuity


def test_continuity_missing_path():
    s = summarize_continuity("demo", video_path=None)
    assert s.status == "skipped"
    assert "Not for employment" in s.disclaimer


def test_continuity_missing_file(tmp_path):
    s = summarize_continuity("demo", video_path=str(tmp_path / "nope.mp4"))
    assert s.status == "skipped"
