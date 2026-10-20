"""Artifact sync must copy timestamped complete reports into the job -o dir."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from verityngn.services.report.artifact_sync import (  # noqa: E402
    ALIAS_REPORT_HTML,
    checklist_artifacts,
    sync_standard_report_artifacts,
)


def test_sync_from_timestamped_complete(tmp_path, monkeypatch):
    vid = "tLJC8hkK-ao"
    debug_root = tmp_path / "outputs_debug" / vid / "2026-10-20_12-00-00_complete"
    debug_root.mkdir(parents=True)
    (debug_root / f"{vid}_report.json").write_text('{"video_id": "%s"}' % vid)
    (debug_root / f"{vid}_report.html").write_text("<html>ok</html>")
    (debug_root / f"{vid}_private_report.html").write_text("<html>priv</html>")

    job_dir = tmp_path / "job_out" / vid
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OUTPUTS_DIR", str(tmp_path / "outputs_debug"))

    result = sync_standard_report_artifacts(job_dir, vid, src_dir=debug_root)
    assert f"{vid}_report.json" in result["copied"]
    assert f"{vid}_report.html" in result["copied"]
    assert (job_dir / f"{vid}_report.json").is_file()
    assert (job_dir / f"{vid}_report.html").is_file()
    assert (job_dir / ALIAS_REPORT_HTML).is_file()
    checks = checklist_artifacts(job_dir, vid)
    assert checks["report_json"]
    assert checks["report_html_alias"]


def test_sync_follows_processing_to_complete(tmp_path):
    vid = "HuangSwap"
    parent = tmp_path / "outputs_debug" / vid
    processing = parent / "2026-10-20_01-00-00_processing"
    complete = parent / "2026-10-20_01-00-00_complete"
    complete.mkdir(parents=True)
    (complete / f"{vid}_report.json").write_text("{}")
    (complete / f"{vid}_report.html").write_text("<html/>")

    out = tmp_path / "o"
    result = sync_standard_report_artifacts(out, vid, src_dir=processing)
    assert result["src_dir"] == str(complete)
    assert (out / f"{vid}_report.json").is_file()
    assert (out / ALIAS_REPORT_HTML).is_file()
