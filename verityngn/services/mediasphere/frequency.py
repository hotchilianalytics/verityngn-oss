"""Appearance frequency counts (YouTube search stub + seeded pilots)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional
import hashlib
import json

from verityngn.services.players.registry import Player


@dataclass
class MediaSphereSnapshot:
    player_id: str
    as_of: str
    window_days: int
    youtube_hit_estimate: int
    news_hit_estimate: int
    method: str
    queries: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _stable_count(seed: str, lo: int, hi: int) -> int:
    h = hashlib.sha256(seed.encode()).hexdigest()
    n = int(h[:8], 16)
    return lo + (n % (hi - lo + 1))


def compute_frequency_counts(
    player: Player,
    *,
    as_of: Optional[date] = None,
    window_days: int = 90,
    live_search: bool = False,
) -> MediaSphereSnapshot:
    """
    Estimate mediasphere frequency for a player.

    Default: deterministic seeded estimates (offline-safe). Optional live_search
    can later wrap yt-dlp / YouTube Data API; kept off for MVP reproducibility.
    """
    as_of = as_of or date.today()
    queries = player.search_queries or [f"{player.name} {player.company}"]
    if live_search:
        # Placeholder hook — do not hit network in default MVP path
        method = "live_search_unimplemented"
        yt = 0
        news = 0
        notes = "live_search requested but not implemented; use seeded path."
    else:
        method = "seeded_hash"
        yt = _stable_count(f"{player.player_id}:{as_of.isoformat()}:yt:{window_days}", 12, 180)
        news = _stable_count(f"{player.player_id}:{as_of.isoformat()}:news:{window_days}", 5, 90)
        notes = (
            "Seeded offline estimates for pilot demos. Replace with yt-dlp/API counts "
            "when credentials and rate limits allow."
        )
    return MediaSphereSnapshot(
        player_id=player.player_id,
        as_of=as_of.isoformat(),
        window_days=window_days,
        youtube_hit_estimate=yt,
        news_hit_estimate=news,
        method=method,
        queries=queries,
        notes=notes,
    )


def write_snapshot(snapshot: MediaSphereSnapshot, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot.to_dict(), indent=2), encoding="utf-8")
    return path


def rolling_daily_series(
    player: Player,
    *,
    end: Optional[date] = None,
    days: int = 30,
    window_days: int = 90,
) -> list[dict[str, Any]]:
    """Produce a short daily frequency series for timeseries join."""
    end = end or date.today()
    rows = []
    for i in range(days):
        d = end - timedelta(days=days - 1 - i)
        snap = compute_frequency_counts(player, as_of=d, window_days=window_days)
        rows.append(snap.to_dict())
    return rows
