"""JSONL feature store keyed by (player_id, ts)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional
import json


@dataclass
class FeatureRow:
    player_id: str
    ts: str  # ISO date
    features: dict[str, Any] = field(default_factory=dict)
    asof_available: str = ""  # information cutoff
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if not d["asof_available"]:
            d["asof_available"] = d["ts"]
        return d


class FeatureStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, row: FeatureRow) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row.to_dict()) + "\n")

    def extend(self, rows: Iterable[FeatureRow]) -> None:
        for r in rows:
            self.append(r)

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out

    def for_player(self, player_id: str) -> list[dict[str, Any]]:
        return [r for r in self.read_all() if r.get("player_id") == player_id]
