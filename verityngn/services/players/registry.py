"""Player registry load/save — multi-entity aware."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional
import json


DEFAULT_DATA = Path(__file__).resolve().parent / "data" / "pilot_ceos.json"


@dataclass
class Entity:
    """Company / platform linked to a player.

    Untradable entities (private companies, platforms) may be attributed in
    mediasphere timelines but must never become prediction targets.
    """

    name: str
    kind: str  # public_company | private_company | platform
    ticker: Optional[str] = None
    tradable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Player:
    player_id: str
    name: str
    role: str
    company: str
    ticker: str
    speaker_id: str = ""
    aliases: list[str] = field(default_factory=list)
    search_queries: list[str] = field(default_factory=list)
    pilot: bool = False
    entities: list[Entity] = field(default_factory=list)
    baseline_video_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["speaker_id"] = self.speaker_id or self.player_id
        return d

    def resolved_speaker_id(self) -> str:
        return self.speaker_id or self.player_id

    def tradable_tickers(self) -> list[str]:
        """Primary ticker plus any additional tradable entity tickers."""
        out: list[str] = []
        if self.ticker:
            out.append(self.ticker.upper())
        for e in self.entities:
            if e.tradable and e.ticker:
                t = e.ticker.upper()
                if t not in out:
                    out.append(t)
        return out

    def untradable_entities(self) -> list[Entity]:
        return [e for e in self.entities if not e.tradable]


class PlayerRegistry:
    def __init__(self, players: Optional[Iterable[Player]] = None) -> None:
        self._by_id: dict[str, Player] = {}
        for p in players or []:
            self.add(p)

    def add(self, player: Player) -> None:
        self._by_id[player.player_id] = player

    def get(self, player_id: str) -> Optional[Player]:
        return self._by_id.get(player_id)

    def by_ticker(self, ticker: str) -> list[Player]:
        t = ticker.upper()
        hits = []
        for p in self._by_id.values():
            if t in p.tradable_tickers():
                hits.append(p)
        return hits

    def pilots(self) -> list[Player]:
        return [p for p in self._by_id.values() if p.pilot]

    def all(self) -> list[Player]:
        return list(self._by_id.values())

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": "1.1", "players": [p.to_dict() for p in self.all()]}

    def write_json(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlayerRegistry":
        players = []
        for raw in data.get("players") or []:
            entities = []
            for e in raw.get("entities") or []:
                entities.append(
                    Entity(
                        name=e["name"],
                        kind=e.get("kind", "public_company"),
                        ticker=e.get("ticker"),
                        tradable=bool(e.get("tradable", True)),
                    )
                )
            # Backward compat: if no entities, synthesize primary company entity
            if not entities and raw.get("ticker"):
                entities = [
                    Entity(
                        name=raw.get("company") or raw.get("ticker"),
                        kind="public_company",
                        ticker=raw.get("ticker"),
                        tradable=True,
                    )
                ]
            players.append(
                Player(
                    player_id=raw.get("player_id") or raw.get("speaker_id"),
                    name=raw["name"],
                    role=raw.get("role", ""),
                    speaker_id=raw.get("speaker_id") or raw.get("player_id") or "",
                    company=raw.get("company", ""),
                    ticker=raw.get("ticker", ""),
                    aliases=list(raw.get("aliases") or []),
                    search_queries=list(raw.get("search_queries") or []),
                    pilot=bool(raw.get("pilot")),
                    entities=entities,
                    baseline_video_ids=list(raw.get("baseline_video_ids") or []),
                )
            )
        return cls(players)

    @classmethod
    def from_json(cls, path: Path) -> "PlayerRegistry":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def load_default_registry(path: Optional[Path] = None) -> PlayerRegistry:
    return PlayerRegistry.from_json(path or DEFAULT_DATA)
