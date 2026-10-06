"""Orchestrate affect extraction for a VerityIndex report JSON."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import json
import re

from verityngn.services.affect.adapters.audeering_vad import extract_dimensional_affect
from verityngn.services.affect.disfluency import extract_disfluency, text_sentiment_proxy
from verityngn.services.affect.exuberance import exuberance_score
from verityngn.services.affect.prosody import ProsodyFeatures, extract_prosody
from verityngn.services.affect.asr import transcribe_audio, words_in_window


DISCLAIMER = (
    "Affect features are research signals for delivery / conviction analysis. "
    "They are not emotion diagnoses, clinical assessments, or veracity judgments."
)


def _parse_timestamp(ts: Any) -> float:
    if ts is None:
        return 0.0
    if isinstance(ts, (int, float)):
        return float(ts)
    s = str(ts).strip()
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)
    parts = s.split(":")
    try:
        parts_f = [float(p) for p in parts]
    except ValueError:
        return 0.0
    if len(parts_f) == 3:
        return parts_f[0] * 3600 + parts_f[1] * 60 + parts_f[2]
    if len(parts_f) == 2:
        return parts_f[0] * 60 + parts_f[1]
    return 0.0


@dataclass
class AffectResult:
    video_id: str
    schema_version: str = "1.0"
    authenticity: dict[str, Any] = field(default_factory=lambda: {"pass": True, "gated": False})
    segments: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "schema_version": self.schema_version,
            "authenticity": self.authenticity,
            "segments": self.segments,
            "summary": self.summary,
            "disclaimer": self.disclaimer,
        }

    def write_json(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path


def extract_affect_for_report(
    report: dict[str, Any] | Path,
    *,
    audio_path: Optional[Path] = None,
    authenticity: Optional[dict[str, Any]] = None,
    window_dur_sec: float = 3.0,
) -> AffectResult:
    if isinstance(report, Path) or (isinstance(report, str) and str(report).endswith(".json")):
        report = json.loads(Path(report).read_text(encoding="utf-8"))
    assert isinstance(report, dict)

    video_id = (
        report.get("video_id")
        or (report.get("metadata") or {}).get("video_id")
        or report.get("media_embed", {}).get("video_id")
        or "unknown"
    )
    claims = (
        report.get("claims_breakdown")
        or report.get("claims")
        or report.get("verified_claims")
        or []
    )
    if claims and isinstance(claims[0], dict) and "claim_text" not in claims[0] and "text" in claims[0]:
        # Signal-report shape uses {text, timestamp} not claims_breakdown.
        pass
    auth = authenticity or {"pass": True, "gated": False, "source": "passthrough"}
    gated = bool(auth.get("gated")) or not bool(auth.get("pass", True))

    # Baseline from first 5s of audio if present
    baseline: Optional[ProsodyFeatures] = None
    wav_path: Optional[Path] = None
    if audio_path and Path(audio_path).exists():
        src = Path(audio_path)
        if src.suffix.lower() not in {".wav", ".wave"}:
            import subprocess
            import tempfile

            wav_path = Path(tempfile.mkstemp(prefix=f"{video_id}_", suffix=".wav")[1])
            try:
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        str(src),
                        "-ac",
                        "1",
                        "-ar",
                        "16000",
                        "-f",
                        "wav",
                        str(wav_path),
                    ],
                    check=True,
                    capture_output=True,
                )
                audio_path = wav_path
            except Exception as exc:  # noqa: BLE001
                import logging

                logging.getLogger(__name__).warning(
                    "[affect] ffmpeg decode failed (%s); using text proxy", exc
                )
                audio_path = None
                try:
                    wav_path.unlink(missing_ok=True)
                except OSError:
                    pass
                wav_path = None
        try:
            if audio_path:
                baseline = extract_prosody(Path(audio_path), window_start_sec=0.0, window_dur_sec=5.0)
        except Exception as exc:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).warning(
                "[affect] baseline prosody failed (%s); using text proxy", exc
            )
            baseline = None
            audio_path = None  # fall through to text-conditioned placeholders

    try:
        return _build_affect_segments(
            video_id=str(video_id),
            claims=claims,
            gated=gated,
            auth=auth,
            audio_path=Path(audio_path) if audio_path else None,
            baseline=baseline,
            window_dur_sec=window_dur_sec,
        )
    finally:
        if wav_path is not None:
            try:
                wav_path.unlink(missing_ok=True)
            except OSError:
                pass


def _build_affect_segments(
    *,
    video_id: str,
    claims: list,
    gated: bool,
    auth: dict[str, Any],
    audio_path: Optional[Path],
    baseline: Optional[ProsodyFeatures],
    window_dur_sec: float,
) -> AffectResult:
    segments: list[dict[str, Any]] = []
    exuberances: list[float] = []
    asr = None
    if audio_path and Path(audio_path).exists() and not gated:
        asr = transcribe_audio(audio_path)
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        text = claim.get("claim_text") or claim.get("text") or ""
        t_sec = _parse_timestamp(claim.get("timestamp"))
        if asr and asr.get("words"):
            win_txt = " ".join(
                words_in_window(asr, max(0.0, t_sec - window_dur_sec), t_sec + window_dur_sec)
            )
            dis = extract_disfluency(win_txt or text)
        else:
            dis = extract_disfluency(text)
        sent = text_sentiment_proxy(text)
        if audio_path and Path(audio_path).exists() and not gated:
            try:
                pros = extract_prosody(
                    Path(audio_path),
                    window_start_sec=max(0.0, t_sec - window_dur_sec / 2),
                    window_dur_sec=window_dur_sec,
                )
            except Exception:  # noqa: BLE001
                pros = ProsodyFeatures(
                    f0_mean=120.0 + 10.0 * sent - 5.0 * dis.rate,
                    f0_std=8.0 + 20.0 * dis.rate,
                    jitter=0.01 + 0.05 * dis.rate,
                    shimmer=0.02 + 0.03 * dis.rate,
                    rate_sps=max(1.0, 4.0 - 2.0 * dis.rate),
                    pause_ratio=min(0.9, 0.2 + dis.rate),
                    energy_mean=0.05 + 0.02 * abs(sent),
                    duration_sec=window_dur_sec,
                )
        else:
            # Text-conditioned placeholder when audio gated/missing: deterministic pseudo-prosody
            # from text length / disfluency so pipelines remain testable offline.
            pros = ProsodyFeatures(
                f0_mean=120.0 + 10.0 * sent - 5.0 * dis.rate,
                f0_std=8.0 + 20.0 * dis.rate,
                jitter=0.01 + 0.05 * dis.rate,
                shimmer=0.02 + 0.03 * dis.rate,
                rate_sps=max(1.0, 4.0 - 2.0 * dis.rate),
                pause_ratio=min(0.9, 0.2 + dis.rate),
                energy_mean=0.05 + 0.02 * abs(sent),
                duration_sec=0.0 if gated else window_dur_sec,
            )
        ex = exuberance_score(
            pros,
            sent,
            baseline_f0=baseline.f0_mean if baseline else None,
            baseline_energy=baseline.energy_mean if baseline else None,
        )
        # Measured dimensional affect (audEERING VAD or prosody proxy)
        if audio_path and Path(audio_path).exists() and not gated:
            dim = extract_dimensional_affect(
                Path(audio_path),
                window_start_sec=max(0.0, t_sec - window_dur_sec / 2),
                window_dur_sec=window_dur_sec,
            )
        else:
            dim = extract_dimensional_affect(None)
        if gated:
            ex = float("nan")
        else:
            exuberances.append(ex)
        segments.append(
            {
                "claim_id": claim.get("claim_id"),
                "timestamp": claim.get("timestamp"),
                "timestamp_sec": t_sec,
                "speaker": claim.get("speaker"),
                "prosody": pros.to_dict(),
                "disfluency": dis.to_dict(),
                "text_sentiment": sent,
                "exuberance": ex,
                "measured_arousal": dim.arousal if not gated else None,
                "measured_valence": dim.valence if not gated else None,
                "measured_dominance": dim.dominance if not gated else None,
                "measured_affect_source": dim.source,
                "gated": gated,
            }
        )

    summary = {
        "n_claims": len(segments),
        "exuberance_mean": float(sum(exuberances) / len(exuberances)) if exuberances else None,
        "disfluency_mean_rate": (
            float(sum(s["disfluency"]["rate"] for s in segments) / len(segments)) if segments else None
        ),
        "audio_used": bool(audio_path and Path(audio_path).exists() and not gated),
        "asr_source": (asr or {}).get("source") if asr else "",
        "gated": gated,
    }
    return AffectResult(video_id=str(video_id), authenticity=auth, segments=segments, summary=summary)
