"""
Predictions report sleeve — per-player dossiers (mirrors deepresearch pattern).
"""
from __future__ import annotations

from verityngn.services.predictions.dossier import PredictionDossier, build_player_dossier
from verityngn.services.predictions.pipeline import run_predictions_pilot

__all__ = ["PredictionDossier", "build_player_dossier", "run_predictions_pilot"]
