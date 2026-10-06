"""Appearance timeline for a player (YouTube / media events)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional
import json


@dataclass
class AppearanceEvent:
    player_id: str
    ts: str  # ISO date or datetime
    source: str  # youtube|news|earnings_call|other
    title: str
    url: Optional[str] = None
    video_id: Optional[str] = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlayerTimeline:
    player_id: str
    events: list[AppearanceEvent] = field(default_factory=list)

    def add(self, event: AppearanceEvent) -> None:
        self.events.append(event)
        self.events.sort(key=lambda e: e.ts)

    def to_dict(self) -> dict[str, Any]:
        return {"player_id": self.player_id, "events": [e.to_dict() for e in self.events]}

    def write_json(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path
