"""Stable video_id for file-upload ingest (OSS CLI + VerityIndex API)."""
from __future__ import annotations

import hashlib
from pathlib import Path


def video_id_from_upload_bytes(data: bytes, filename: str) -> str:
    """Hash first 64 KiB + filename — matches VerityIndex ingest API."""
    h = hashlib.sha256()
    h.update(data[: min(len(data), 65536)])
    h.update(filename.encode())
    return h.hexdigest()[:11]


def video_id_from_file_path(path: str | Path) -> str:
    p = Path(path)
    return video_id_from_upload_bytes(p.read_bytes(), p.name)
