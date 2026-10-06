"""End-to-end pilot orchestration for Predictions sleeves."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import json

from verityngn.services.mediasphere.frequency import compute_frequency_counts, rolling_daily_series, write_snapshot
from verityngn.services.mediasphere.velocity import compute_velocity
from verityngn.services.players.registry import load_default_registry
from verityngn.services.predictions.dossier import build_player_dossier
from verityngn.services.timeseries.earnings import write_fixtures
from verityngn.services.timeseries.event_study import run_event_study
from verityngn.services.timeseries.store import FeatureRow, FeatureStore


def run_predictions_pilot(
    out_dir: Path,
    *,
    affect_dir: Optional[Path] = None,
) -> dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    registry = load_default_registry()
    registry.write_json(out_dir / "players" / "registry.json")

    write_fixtures(out_dir / "timeseries" / "earnings_fixtures.json")
    store = FeatureStore(out_dir / "timeseries" / "features.jsonl")

    affect_summaries_by_player: dict[str, list[dict[str, Any]]] = {p.player_id: [] for p in registry.pilots()}
    # Gallery affect is video-centric; attach all gallery summaries as shared context for pilots in MVP
    shared_affect: list[dict[str, Any]] = []
    if affect_dir and Path(affect_dir).exists():
        for p in sorted(Path(affect_dir).glob("*_affect.json")):
            data = json.loads(p.read_text(encoding="utf-8"))
            shared_affect.append(
                {
                    "video_id": data.get("video_id"),
                    "exuberance_mean": (data.get("summary") or {}).get("exuberance_mean"),
                    "gated": (data.get("summary") or {}).get("gated"),
                    "path": str(p),
                }
            )

    dossiers = {}
    mediasphere_out = {}
    for player in registry.pilots():
        snap = compute_frequency_counts(player, window_days=90)
        write_snapshot(snap, out_dir / "mediasphere" / f"{player.player_id}_freq.json")
        series = rolling_daily_series(player, days=30, window_days=90)
        (out_dir / "mediasphere" / f"{player.player_id}_series.json").write_text(
            json.dumps(series, indent=2), encoding="utf-8"
        )
        vel = compute_velocity(series)
        mediasphere_out[player.player_id] = {"snapshot": snap.to_dict(), "velocity": vel}

        # Feature store rows (latest day)
        latest = series[-1] if series else snap.to_dict()
        store.append(
            FeatureRow(
                player_id=player.player_id,
                ts=latest.get("as_of") or snap.as_of,
                features={
                    "youtube_hit_estimate": latest.get("youtube_hit_estimate"),
                    "news_hit_estimate": latest.get("news_hit_estimate"),
                    "mediasphere_velocity": vel.get("velocity"),
                    "exuberance_mean": (
                        shared_affect[0]["exuberance_mean"] if shared_affect else None
                    ),
                },
                asof_available=latest.get("as_of") or snap.as_of,
                source="pilot_mvp",
            )
        )

        # Prediction targets only tradable tickers (exclude private/platform entities)
        tradable = player.tradable_tickers()
        pred = {
            "direction": "insufficient_evidence",
            "confidence": 0.0,
            "target": "next_earnings_surprise_direction",
            "tradable_tickers": tradable,
            "excluded_entities": [e.to_dict() for e in player.untradable_entities()],
            "trial_id": "T000",
            "note": "Harness registered; wait for linked earnings-call affect before claiming direction.",
        }
        dossier = build_player_dossier(
            player.to_dict(),
            mediasphere=snap.to_dict(),
            velocity=vel,
            affect_summaries=shared_affect,
            deception={
                "overall_band": "n/a",
                "overall_score": None,
                "note": "Attach gallery deception_risk JSON when available.",
            },
            prediction=pred,
        )
        paths = dossier.write(out_dir / "dossiers")
        dossiers[player.player_id] = {k: str(v) for k, v in paths.items()}

    study = run_event_study(trial_id="T000", allow_synthetic=True)
    study_path = out_dir / "timeseries" / "event_study_T000.json"
    study_path.write_text(json.dumps(study.to_dict(), indent=2), encoding="utf-8")

    manifest = {
        "dossiers": dossiers,
        "mediasphere": mediasphere_out,
        "event_study": str(study_path),
        "feature_store": str(store.path),
        "affect_linked": shared_affect,
    }
    (out_dir / "pilot_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
