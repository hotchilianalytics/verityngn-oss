"""Build per-player prediction dossiers with Limits section."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import json


LIMITS_MD = """
## Limits

- Affect / exuberance features are **research delivery signals**, not emotion diagnoses.
- `deception_risk` is a **congruence / delivery-risk band** — **not** a lie detector and must not be read as a finding that a named executive is lying.
- Authenticity gate: affect features are excluded when deepfake / provenance checks fail.
- Predictive metrics shown here are **harness / fixture results** unless a registered trial in `docs/trials_ledger.md` says otherwise. No tradable alpha claim.
- Emotion-recognition regulation (incl. EU AI Act Art. 5(1)(f)) prohibits biometric emotion inference in **workplace and education**; this product is markets/research analytics and is **not for employment, HR, or education screening**.
- Untradable entities (private companies, platforms) may appear in mediasphere attribution but are excluded from prediction targets.
""".strip()


@dataclass
class PredictionDossier:
    player_id: str
    title: str
    sections: dict[str, Any] = field(default_factory=dict)
    markdown: str = ""

    def write(self, out_dir: Path) -> dict[str, Path]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        base = out_dir / f"{self.player_id}_prediction_dossier"
        json_path = Path(str(base) + ".json")
        md_path = Path(str(base) + ".md")
        json_path.write_text(
            json.dumps({"player_id": self.player_id, "title": self.title, **self.sections}, indent=2),
            encoding="utf-8",
        )
        md_path.write_text(self.markdown, encoding="utf-8")
        return {"json": json_path, "md": md_path}


def build_player_dossier(
    player: dict[str, Any],
    *,
    mediasphere: Optional[dict[str, Any]] = None,
    velocity: Optional[dict[str, Any]] = None,
    affect_summaries: Optional[list[dict[str, Any]]] = None,
    deception: Optional[dict[str, Any]] = None,
    event_study: Optional[dict[str, Any]] = None,
    prediction: Optional[dict[str, Any]] = None,
) -> PredictionDossier:
    player_id = player["player_id"]
    name = player.get("name", player_id)
    title = f"VerityIndex Predictions — {name} ({player.get('ticker', '')})"

    pred = prediction or {
        "direction": "insufficient_evidence",
        "confidence": 0.0,
        "target": "next_earnings_surprise_direction",
        "trial_id": None,
    }

    sections = {
        "player": player,
        "mediasphere": mediasphere or {},
        "velocity": velocity or {},
        "affect_summaries": affect_summaries or [],
        "deception_risk": deception or {},
        "event_study": event_study or {},
        "prediction": pred,
        "disclaimer": (
            "Congruence / conviction / delivery-risk only. Not a lie detector. "
            "Not investment advice."
        ),
        "limits": LIMITS_MD,
    }

    entities = player.get("entities") or []
    entity_lines = []
    for e in entities:
        tag = "tradable" if e.get("tradable", True) else "UNTRADABLE — not a prediction target"
        ticker = e.get("ticker") or "—"
        entity_lines.append(f"- {e.get('name')} ({e.get('kind')}, `{ticker}`) — {tag}")

    md_lines = [
        f"# {title}",
        "",
        f"**Role:** {player.get('role')} @ {player.get('company')} (`{player.get('ticker')}`)",
        "",
        "## Entities",
    ]
    md_lines.extend(entity_lines or ["- (primary ticker only)"])
    md_lines += [
        "",
        "## Media-sphere",
        f"- YouTube hit estimate (window): {(mediasphere or {}).get('youtube_hit_estimate', 'n/a')}",
        f"- News hit estimate: {(mediasphere or {}).get('news_hit_estimate', 'n/a')}",
        f"- Velocity: {(velocity or {}).get('velocity', 'n/a')}",
        "",
        "## Affect / exuberance (summary)",
    ]
    if affect_summaries:
        for a in affect_summaries:
            md_lines.append(
                f"- `{a.get('video_id')}`: exuberance_mean={a.get('exuberance_mean')}, "
                f"gated={a.get('gated')}"
            )
    else:
        md_lines.append("- No linked affect runs yet (pilot may use gallery proxies).")

    md_lines += [
        "",
        "## Congruence / delivery-risk",
        f"- Overall band: {(deception or {}).get('overall_band', 'n/a')}",
        f"- Overall score: {(deception or {}).get('overall_score', 'n/a')}",
        "",
        "## Prediction",
        f"- Target: {pred.get('target')}",
        f"- Direction: **{pred.get('direction')}**",
        f"- Confidence: {pred.get('confidence')}",
        f"- Trial: {pred.get('trial_id')}",
        "",
        LIMITS_MD,
        "",
    ]

    return PredictionDossier(player_id=player_id, title=title, sections=sections, markdown="\n".join(md_lines))
