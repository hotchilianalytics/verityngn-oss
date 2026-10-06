#!/usr/bin/env python3
"""Re-run measured VAD + faster-whisper ASR on Karp local media.

Does not call Gemini. Writes {video_id}_affect.json then stamps audio_source /
asr_source onto the corpus report videos[] so score_signal_quality can re-score L.

Usage (verityngn env):

  export PYTHONPATH=.
  python scripts/predictions/run_measured_affect_karp.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VIDEO_IDS = [
    "QNkPpVYagRc",
    "dRgPbNJ5RJc",
    "V7mYWOzdhpc",
    "ijRuuaaM6XM",
    "xe84cwQJKaE",
    "WBu9Ai6OX3I",
    "pHu-FarYZlU",
]


def _find_report(out_dir: Path, vid: str) -> Path | None:
    candidates = [
        out_dir / f"{vid}_report_with_delivery.json",
        out_dir / f"{vid}_report.json",
        out_dir / f"{vid}_final_report.json",
        out_dir / "ceo_pltr_karp_signal_report.json",
    ]
    scored: list[tuple[int, Path]] = []
    for p in candidates:
        if not p.exists():
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(obj, dict):
            continue
        claims = obj.get("claims_breakdown") or obj.get("claims")
        n = len(claims) if isinstance(claims, list) else 0
        scored.append((n, p))
    if not scored:
        return None
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[0][1]


def _media_ok(path: Path, *, min_bytes: int = 1_000_000) -> bool:
    try:
        return path.exists() and path.stat().st_size >= min_bytes
    except OSError:
        return False


def _find_media(out_dir: Path, vid: str) -> Path | None:
    media_dir = out_dir / "media"
    if not media_dir.is_dir():
        return None
    for ext in (".mp4", ".wav", ".m4a", ".webm", ".mkv"):
        p = media_dir / f"{vid}{ext}"
        if _media_ok(p):
            return p
    hits = sorted(p for p in media_dir.glob(f"{vid}.*") if _media_ok(p) and not str(p).endswith(".part"))
    return hits[0] if hits else None


def _yt_dlp_bin() -> str:
    env = os.environ.get("VN_YT_DLP")
    if env and Path(env).exists():
        return env
    found = shutil.which("yt-dlp")
    return found or "yt-dlp"


def download_media(out_dir: Path, vid: str) -> Path | None:
    """Fetch local mp4. Format-18 stubs (<1MB) are rejected.

    Working recipe (2026-08-15, yt-dlp 2026.7.4): Node EJS + tv_downgraded/web_safari
    + live Chrome cookies. cookies.txt is often too stale for this client.
    """
    existing = _find_media(out_dir, vid)
    if existing is not None:
        return existing
    media_dir = out_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    dest = media_dir / f"{vid}.mp4"
    cookies = ROOT / "cookies.txt"
    cookie_file = cookies if cookies.exists() else None
    import subprocess

    attempts: list[list[str]] = [
        [
            _yt_dlp_bin(),
            "--js-runtimes", "node",
            "--extractor-args", "youtube:player_client=tv_downgraded,web_safari",
            "-f", "b/bv*+ba/best",
            "--merge-output-format", "mp4",
            "--force-ipv4",
            "--retries", "20",
            "--no-part",
            "-o", str(dest),
            f"https://www.youtube.com/watch?v={vid}",
        ],
        [
            _yt_dlp_bin(),
            "-f", "18/bestaudio/best",
            "--extractor-args", "youtube:player_client=android_vr,web_safari",
            "-o", str(dest),
            "--no-progress",
            "--no-update",
            f"https://www.youtube.com/watch?v={vid}",
        ],
    ]
    if cookie_file is not None:
        for cmd in attempts:
            cmd[1:1] = ["--cookies", str(cookie_file)]

    log = out_dir / "download_media.log"
    for idx, cmd in enumerate(attempts):
        print(f"[measured] downloading {vid} attempt={idx} -> {dest}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        extra = f"\n# attempt={idx} rc={r.returncode}\n"
        log.write_text(
            (log.read_text(encoding="utf-8") if log.exists() else "")
            + extra
            + (r.stdout or "")
            + "\n"
            + (r.stderr or ""),
            encoding="utf-8",
        )
        got = dest if dest.exists() else _find_media(out_dir, vid)
        if got is not None and _media_ok(got):
            return got
        if dest.exists() and not _media_ok(dest):
            try:
                dest.unlink()
            except OSError:
                pass
        print(f"[measured] yt-dlp {vid} attempt={idx} too small or failed rc={r.returncode}")
    return _find_media(out_dir, vid)


def main() -> int:
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    os.chdir(ROOT)
    from collections import Counter

    from verityngn.services.affect.extract import extract_affect_for_report

    only = os.environ.get("KARP_VIDEO_ID", "").strip()
    many = os.environ.get("KARP_VIDEO_IDS", "").strip()
    if many:
        vids = [v.strip() for v in many.split(",") if v.strip()]
    elif only:
        vids = [only]
    else:
        vids = list(VIDEO_IDS)
    stamps: dict[str, dict] = {}
    want_dl = os.environ.get("KARP_DOWNLOAD", "1") not in {"0", "false", "False"}

    for vid in vids:
        out_dir = ROOT / ".outputs" / f"karp_local_{vid}"
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = _find_report(out_dir, vid)
        media = _find_media(out_dir, vid)
        if media is None and want_dl:
            media = download_media(out_dir, vid)
        print(f"[measured] {vid} report={report_path} media={media}")
        if report_path is None or media is None:
            stamps[vid] = {"skipped": True, "reason": "missing report or media"}
            continue
        affect = extract_affect_for_report(report_path, audio_path=media)
        dest = out_dir / f"{vid}_affect.json"
        affect.write_json(dest)
        payload = affect.to_dict()
        segs = [s for s in (payload.get("segments") or []) if isinstance(s, dict)]
        sources = [str(s.get("measured_affect_source") or "") for s in segs]
        sources = [s for s in sources if s]
        audio_src = Counter(sources).most_common(1)[0][0] if sources else ""
        asr_src = str((payload.get("summary") or {}).get("asr_source") or "")
        stamp = {
            "audio_source": audio_src,
            "asr_source": asr_src,
            "audio_used": (payload.get("summary") or {}).get("audio_used"),
            "n_segments": len(segs),
            "affect_path": str(dest),
        }
        stamps[vid] = stamp
        print(f"[measured] {vid} -> {stamp}")

    stamp_path = ROOT / ".outputs" / "measured_affect_stamps.json"
    t014 = ROOT / ".outputs" / "measured_affect_t014_stamps.json"
    stamp_path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    for p in (t014, stamp_path):
        if p.exists():
            try:
                blob = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(blob, dict):
                    existing.update(blob)
            except (OSError, json.JSONDecodeError):
                pass
    existing.update(stamps)
    stamps = existing
    stamp_path.write_text(json.dumps(stamps, indent=2), encoding="utf-8")
    print(f"[measured] wrote {stamp_path}")

    corpus = ROOT / ".outputs" / "ceo_pltr_karp_corpus" / "ceo_pltr_karp_signal_report.json"
    if corpus.exists():
        report = json.loads(corpus.read_text(encoding="utf-8"))
        live_qnk = ROOT / ".outputs" / "live_gemini_compare_QNkPpVYagRc" / "compare.json"
        qnk_live = False
        if live_qnk.exists():
            live = json.loads(live_qnk.read_text(encoding="utf-8"))
            qnk_live = bool(live.get("live_gemini_true")) or bool(
                (live.get("live") or {}).get("live_gemini")
            )
        for v in report.get("videos") or []:
            if not isinstance(v, dict):
                continue
            vid = str(v.get("video_id") or "")
            st = stamps.get(vid) or {}
            if st.get("audio_source"):
                v["audio_source"] = st["audio_source"]
                v["measured_affect_source"] = st["audio_source"]
            if st.get("asr_source"):
                v["asr_source"] = st["asr_source"]
            if vid == "QNkPpVYagRc" and qnk_live:
                v["live_gemini"] = True
        report["trial"] = os.environ.get("KARP_TRIAL", "T015")
        corpus.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[measured] stamped {corpus}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
