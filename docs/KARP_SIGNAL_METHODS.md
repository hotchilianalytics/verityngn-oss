# Karp multimodal methods synopsis

Technical record of the local workflow used for `ceo_pltr_karp`. Companion to [KARP_SIGNAL_VOCAB.md](KARP_SIGNAL_VOCAB.md).

## Pipeline (one video)

```
YouTube URL
    │
    ├─ yt-dlp android client → local mp4 (affect only)
    │
    └─ run_verification (LangGraph)
           Stage 1  Vertex Gemini multimodal claims (YouTube URL + VideoMetadata)
           Stage 2  Counter-intel (CSE + YouTube search)
           Stage 3  Claim ranking / temporal enforce
           Stage 4  Per-claim web verification
           Stage 5  Unified HTML/MD/JSON report
           Stage 6  Local save (no GCS in research mode)
    │
    └─ run_multisense (MULTISENSE_ENABLED=1)
           Gemini Tier A (whole video)
           Gemini Tier B (claim ±15s windows, capped)
           extract_affect_for_report (ffmpeg mp4→16 kHz mono WAV)
           build_fused_index (align + crossmodal + arcs)
```

Entry: `scripts/run_local_karp_multisense.py`  
Env: `MULTISENSE_ENABLED=1`, Vertex via `GOOGLE_APPLICATION_CREDENTIALS` / `GOOGLE_CLOUD_PROJECT`.  
`MULTISENSE_OFFLINE=1` forces deterministic proxies (CI).

## Stage methods

### Claims (interpreted, veracity)

| Piece | Method |
|-------|--------|
| Input | Public YouTube URI to Vertex (`USE_VERTEX_YOUTUBE_URL`, segmented) |
| Model | `LLM_MODEL` from `.env` (e.g. `gemini-3-flash-preview`) |
| Segmentation | Duration-aware token budget (`verityngn/config/video_segmentation.py`); ~14 min → 1 segment; ~35 min still typically 1–2 |
| Claims | Factual extraction, dedupe, max-claims cap |
| Verification | Google CSE + news/site restrictors; counter-intel once; probability model TRUE/FALSE/UNCERTAIN |
| Output | `{video_id}_report.json` under `outputs_debug/{id}/{stamp}_complete/` |

PDF may fail locally if Playwright Chromium is missing; HTML/JSON still write.

### Tier A — whole-video delivery track (interpreted)

File: `verityngn/services/fusion/gemini_multisense.py`

- Prompt asks for ~15–45s speaking segments: `start_sec`, `end_sec`, speaker, Plutchik `vocal_emotion`, arousal 0–1, valence −1–1, delivery bands, `delivery_style`, confidence.
- Video part: `FileData(file_uri=youtube_url, mime_type=video/youtube)` + optional `VideoMetadata` offsets.
- JSON parse with fence strip; `_normalize_delivery` fills missing bands.
- `_emotion_to_sr` maps Plutchik primary → Spot Runner leaf ids.

### Tier B — claim clips (interpreted)

- Windows: `clip_windows.build_clip_windows` (claim timestamp ±15s, merge overlap, `tier_b_windows` cap).
- Prompt braces escaped so `.format(claim_text, start_sec, end_sec)` cannot collide with `{pace_band,…}`.
- Returns spoken paraphrase, OCR list, facial/gesture prose, `congruence_score`, `vocal_delivery`.
- Observational alignment only.

### Measured affect

Files: `affect/extract.py`, `affect/prosody.py`, `affect/exuberance.py`, `affect/disfluency.py`, `affect/adapters/audeering_vad.py`

| Step | Method |
|------|--------|
| Decode | ffmpeg → 16 kHz mono WAV (mp4 is not RIFF; `wave.open` would fail) |
| Prosody | Autocorr F0, energy, pause_ratio, shimmer; window at claim ±1.5s (default 3s) |
| Baseline | First 5s of file |
| Exuberance | Energy/F0 vs baseline (`exuberance_score`) |
| Disfluency | Regex on **claim text** (um/uh), not ASR |
| Dimensional VAD | `extract_dimensional_affect` — currently **`prosody_proxy`** if audEERING weights absent |

`f0_mean` may be NaN on compressed broadcast audio; exuberance still uses energy.

### Fusion

Files: `fusion/align.py`, `fusion/crossmodal.py`, `fusion/schema.py`, `fusion/arcs.py`, `fusion/plutchik.py`

1. Align claim timestamps with nearest Gemini segment + affect row.
2. `score_crossmodal`: text–voice–face divergences, `congruence`, `congruence_multiplier`, `interpreted_measured` (arousal/valence agreement), within-video z, `delivery_risk_band`.
3. Story arcs from dominant SR segments.
4. Write `{id}_fused_index.json`.

### S11 — discourse derailment (Krykoniuk et al. 2026)

File: `verityngn/services/fusion/derailment.py`

Paper: [Humanit Soc Sci Commun 2026](https://www.nature.com/articles/s41599-026-07900-x) ([The Conversation](https://theconversation.com/ai-is-making-disinformation-harder-to-spot-but-weve-found-a-new-way-to-catch-it-288671)). Method: LLM generates expected replies to a comment; distance to the *actual* reply is derailment (red herring 36%, non sequitur 65% of derailing posts in their BBC YouTube set). ~77% vs human labels; **different cues / bias** vs annotators.

CEO-panel adaptation (not comment threads): interviewer question = expected topic; Karp answer = actual reply. Live path: Gemini writes 3 expected on-topic replies and a 0–1 score. Offline: `1 − Jaccard(tokens)`. **Never** a disinformation or lie label.

### Signal registry (S01–S11)

File: `scripts/build_karp_signal_report.py`

Per video: load four JSONs + claims report → 10 signals + matplotlib charts (base64 in HTML).

Corpus rollup (`--corpus-dirs`):

- Numeric signals: **unweighted mean** across videos + min/max range.
- Dict-valued signals (S04, S06, S08, S10): keep prototype + `by_video`.
- Charts: per-video congruence vs Q&A delta; pooled emotion minutes.
- Output dir: `.outputs/ceo_pltr_karp_corpus/`

Topic tags (S04): keyword hit on OCR + claim text (`israel/war/…` vs `palantir/aip/…`). CNBC `QNkPpVYagRc` still falls back to 530s time cut if keywords miss.

## Local download note

yt-dlp `web`/`mweb` often SABR-block. `player_client=android` is first in `video_service.py` for local mp4. Gemini claims still use the YouTube URL (no need to upload the file to Vertex).

## Known biases / gaps

| Issue | Effect |
|-------|--------|
| `prosody_proxy` valence | Mildly positive even when Gemini is angry → S02 `valence_gap` |
| Interviewer in claim set | Sorkin lines enter within-video z |
| Text disfluency | S07 stuck at 0 on short claims |
| No AU / gaze / blink | S09 is Gemini prose, not FACS |
| n=2 still tiny | Rolling Karp z needs ≥5 videos before promote discussion |
| Hardcoded CNBC cut | Replaced by keywords for new videos; leftover fallback only for `QNkPpVYagRc` |

## Reproduce

```bash
cd ~/.cursor/worktrees/predictions-f487c957/verityngn-core-commercial-2c6d35116c0f
conda activate verityngn
set -a && source .env && set +a
export PYTHONPATH=. MULTISENSE_ENABLED=1
export KARP_VIDEO_ID=dRgPbNJ5RJc
python scripts/run_local_karp_multisense.py

python scripts/build_karp_signal_report.py --corpus-dirs \
  .outputs/karp_local_QNkPpVYagRc \
  .outputs/karp_local_dRgPbNJ5RJc \
  --out-dir .outputs/ceo_pltr_karp_corpus
```

## Citations (roadmap sensors, not currently in the run)

- Discourse derailment / Discourser — [Krykoniuk et al. 2026](https://www.nature.com/articles/s41599-026-07900-x) (S11, live)
- Whissle visual lane (gaze/blink/pose) — [arXiv:2606.22699](https://arxiv.org/html/2606.22699v1)
- Multimodal AU + voice — [arXiv:2407.06005](https://arxiv.org/html/2407.06005v1)
- CEO interview modal incongruence — [Oxford-Man 2026 draft](https://oxford-man.ox.ac.uk/wp-content/uploads/2026/06/Siew-Modal-Incongruence-Oxford-Conference-Draft-20260610.pdf)
- Behavioral vs EEG fusion — [Sci Rep 2025](https://www.nature.com/articles/s41598-025-92399-6)
