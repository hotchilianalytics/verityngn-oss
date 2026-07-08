"""Tests for unified file-upload video_id."""
from verityngn.utils.upload_id import video_id_from_upload_bytes


def test_video_id_from_upload_bytes_stable():
    data = b"fake mp4 header" * 100
    vid = video_id_from_upload_bytes(data, "deposition.mp4")
    assert len(vid) == 11
    assert vid == video_id_from_upload_bytes(data, "deposition.mp4")


def test_video_id_differs_by_filename():
    data = b"same content"
    assert video_id_from_upload_bytes(data, "a.mp4") != video_id_from_upload_bytes(data, "b.mp4")
