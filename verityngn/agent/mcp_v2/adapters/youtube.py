"""YouTube Data API: owned-channel uploads only.

Walks a channel's uploads playlist with ``channels.list`` then
``playlistItems.list`` (one quota unit each). Never calls ``search.list``, never
aggregates across channels, and never persists anything but ``video_id``.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import urllib.parse
from pathlib import Path
from typing import Any, Optional

from verityngn.agent.mcp_v2.adapters.http import request_json
from verityngn.agent.mcp_v2.errors import ToolFailure

API = "https://www.googleapis.com/youtube/v3"
_REGISTRY_ENV = "SPLITRISK_OWNED_CHANNELS"
_BUNDLED = Path(__file__).resolve().parent.parent / "data" / "owned_channels.json"


class OwnedChannelRegistry:
    """Curated registry: a channel counts only if the issuer's own site links to it, or after manual review.

    File format: ``{"<cik>": [{"channel_id": "...", "verified_by": "issuer_site_link", "evidence_url": "..."}]}``.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self._entries: dict[str, list[dict[str, Any]]] = {}
        for p in (_BUNDLED, path or (Path(os.environ[_REGISTRY_ENV]) if os.environ.get(_REGISTRY_ENV) else None)):
            if p and p.is_file():
                data = json.loads(p.read_text(encoding="utf-8"))
                for cik, rows in (data.get("issuers") or data).items():
                    if not str(cik).isdigit():
                        continue
                    self._entries.setdefault(str(int(cik)), []).extend(rows)

    def channels(self, cik: Optional[str]) -> list[dict[str, Any]]:
        if not cik:
            return []
        out = []
        for row in self._entries.get(str(int(cik)), []):
            if row.get("verified_by") in ("issuer_site_link", "manual_review") and row.get("channel_id"):
                out.append({"platform": "youtube", "channel_id": row["channel_id"], "verified_by": row["verified_by"]})
        return out


class YouTubeUploads:
    provider = "YouTube Data API"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("YOUTUBE_API_KEY") or os.environ.get("YOUTUBE_DATA_API_KEY")

    def _get(self, method: str, **params: Any) -> Any:
        if not self.api_key:
            raise ToolFailure(
                "UPSTREAM",
                "YouTube listing is not configured on this server (no YouTube Data API key).",
                alternative="Paste a video ID from the company's channel into analyze_video, or upload the video with register_document.",
            )
        params["key"] = self.api_key
        return request_json(f"{API}/{method}?" + urllib.parse.urlencode(params), provider=self.provider)

    def uploads(self, channel_id: str, start: dt.date, end: dt.date, max_results: int) -> list[dict[str, Any]]:
        chans = self._get("channels", part="contentDetails", id=channel_id)
        items = chans.get("items") or []
        if not items:
            raise ToolFailure("NOT_FOUND", f"YouTube channel {channel_id} not found.")
        playlist = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        out: list[dict[str, Any]] = []
        token: Optional[str] = None
        for _ in range(10):
            params: dict[str, Any] = {"part": "snippet,contentDetails", "playlistId": playlist, "maxResults": 50}
            if token:
                params["pageToken"] = token
            page = self._get("playlistItems", **params)
            stop = False
            for it in page.get("items") or []:
                cd = it.get("contentDetails") or {}
                published = cd.get("videoPublishedAt") or (it.get("snippet") or {}).get("publishedAt") or ""
                day = published[:10]
                if day and day > end.isoformat():
                    continue
                if day and day < start.isoformat():
                    stop = True
                    break
                out.append(
                    {
                        "video_id": cd.get("videoId") or ((it.get("snippet") or {}).get("resourceId") or {}).get("videoId"),
                        "channel_id": channel_id,
                        "title": (it.get("snippet") or {}).get("title", ""),
                        "published_at": published,
                    }
                )
                if len(out) >= max_results:
                    return out
            token = page.get("nextPageToken")
            if stop or not token:
                break
        return out

    def published_date(self, video_id: str) -> Optional[str]:
        if not self.api_key:
            return None
        try:
            data = self._get("videos", part="snippet", id=video_id)
        except ToolFailure:
            return None
        items = data.get("items") or []
        return (items[0].get("snippet") or {}).get("publishedAt", "")[:10] if items else None
