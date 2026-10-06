# VerityIndex Predictions — Design

**Status:** Multimodal extension (vision + fusion + quant) — 2026-08-06  
**Partners:** Derrick Horner / H1 Ventures (co-development)  
**Base:** VerityIndex OSS claims pipeline + Deep Research sleeve pattern  
**Branch / worktree:** `verityindex-predictions`

## Thesis

Prior art (Speech Craft Analytics and related earnings-call vocal-feature literature) shows CEO/CFO prosody in Q&A can predict short-horizon excess returns orthogonal to text sentiment. VerityIndex Predictions extends the existing multimodal claims pipeline with:

1. **Affect / exuberance indexing** around claim timestamps  
2. **Media-sphere frequency / velocity** for named players (C-suite)  
3. **Congruence / delivery-risk** signals (not lie detection)  
4. **Leakage-safe time-series** joining those features to company outcomes (earnings surprises)
5. **Discourse derailment (S11)** — Krykoniuk, Hopkin-King & Roberts 2026 ([Nature HSS Comms](https://www.nature.com/articles/s41599-026-07900-x)): LLM expected replies vs actual Q&A as a topic-shift cue. **Not** a disinformation detector.

## Architecture

Sleeves parallel to `verityngn/services/deepresearch/`:

| Sleeve | Path | Role |
|--------|------|------|
| Affect | `services/affect/` | Prosody, text emotion, exuberance composite |
| Deception | `services/deception/` | Congruence, disfluency, baseline deviation → `deception_risk` band |
| Authenticity | `services/authenticity/` | Deepfake / provenance gate before affect scoring |
| Players | `services/players/` | Person ↔ role ↔ company ↔ ticker registry + timeline |
| Mediasphere | `services/mediasphere/` | Appearance frequency / velocity time series |
| Timeseries | `services/timeseries/` | Feature store, earnings join, event study, baselines |
| Predictions report | `services/predictions/` | Per-player dossier (mirrors deepresearch outputs) |

```
media decoder → authenticity gate → affect → timeseries
claims pipeline → affect / deception → timeseries
players → mediasphere → timeseries
timeseries → predictions dossier
```

## Signal taxonomy (two tiers)

### Tier 1 — Open measured features (ship by default)

- Audio: pitch (F0 mean/std), jitter, shimmer, speaking rate, pause ratio  
- Text: sentiment polarity/arousal proxies, disfluency markers (uh/um/like clusters)  
- Cross-modal: text–voice divergence (sentiment vs arousal mismatch)  
- Delivery: Q&A vs scripted-segment baseline deviation  
- Media: appearance counts, velocity (Δ appearances / window)  
- Composite: **exuberance** = normalized arousal × positive valence around claim windows  
- Output labels: `congruence`, `conviction`, `delivery_risk` bands — **never** “lying”

### Tier 2 — Vendor interpreted constructs (optional, labeled)

| Vendor | Adapter | Construct | Notes |
|--------|---------|-----------|-------|
| millionways.ai (Thorsten-4) | `affect/adapters/millionways.py` | Emotion / affect vectors | First partner; self-hostable API |
| Corsound AI | `authenticity/adapters/corsound.py` | Voice deepfake score | Gate input |
| Nemesysco LVA | `deception/adapters/nemesysco.py` | Licensed stress / LVA | Optional; clearly labeled vendor construct |
| Revealense Illuminator | `deception/adapters/revealense.py` | Licensed facial/micro signals | Optional; labeled |

Tier-2 outputs must carry `source: vendor:<name>` and `construct_type: interpreted` in JSON. They never overwrite Tier-1 fields.

## Compliance guardrails (non-negotiable)

1. **No lie-detector language** in UI, API, or dossiers. Prefer congruence / conviction / delivery-risk.  
2. **Emotion-recognition disclaimer** on every affect surface; EU AI Act awareness (emotion recognition in workplace / biometric contexts is high-risk / restricted in many jurisdictions — product is research/markets analytics, not HR screening).  
3. **Authenticity gate:** if deepfake / provenance fail → affect features are marked `gated=true` and excluded from prediction features.  
4. **Named-executive defamation hygiene:** never assert that a named person is “lying”; ship evidence bands + methodology limits.  
5. **Trials ledger + leakage discipline** for any predictive claim shown to H1 (`docs/trials_ledger.md`).

## Leakage-safe time series

Same hygiene as quant research:

- Features at time *t* may only use information available at *t* (causal transforms)  
- Earnings event study: features from call window must not include post-announcement returns when predicting surprise  
- Train / validate / test splits by time; no random shuffle across events  
- Report deflated Sharpe / multiple-testing aware metrics when claiming alpha  
- Every experiment registered in `docs/trials_ledger.md` before peeking at test metrics

## Phases

| Phase | Deliverable |
|-------|-------------|
| P0 | Module dirs + this design doc |
| P1 | Affect MVP on 2–3 gallery videos → `{video_id}_affect.json` |
| P2 | Players registry + mediasphere counts for 3 pilot CEOs |
| P3 | Timeseries store + earnings ground truth + event-study harness |
| P4 | Vendor adapter interface (millionways first; stubs for others) + authenticity gate |
| P5 | Pilot CEO dossier + H1 Ventures demo doc |

## Pilot CEOs (P2/P5 → multimodal extension)

| player_id | Name | Role | Company | Ticker | Entities |
|-----------|------|------|---------|--------|----------|
| ceo_aapl_cook | Tim Cook | CEO | Apple Inc. | AAPL | Apple (tradable) |
| ceo_msft_nadella | Satya Nadella | CEO | Microsoft Corp. | MSFT | Microsoft (tradable) |
| ceo_nvda_huang | Jensen Huang | CEO | NVIDIA Corp. | NVDA | NVIDIA (tradable) |
| ceo_pltr_karp | Alex Karp | CEO | Palantir Technologies | PLTR | Palantir (tradable) |
| ceo_tsla_musk | Elon Musk | CEO | Tesla, Inc. | TSLA | Tesla (tradable); xAI, SpaceX, X (**untradable**) |

`Player.entities` is multi-entity aware; untradable entities may appear in mediasphere attribution but never become prediction targets.

## Multimodal extension (2026-08-06)

### Additional sleeves

| Sleeve | Path | Role |
|--------|------|------|
| Vision | `services/vision/` | Landmarks, FACS AUs, gaze/blink, rPPG + sympathetic arousal, OCR/geo |
| Fusion | `services/fusion/` | Align, Plutchik `sr_*` taxonomy + closure, story arcs, cross-modal congruence |
| Quant | `services/quant/` | PIT media factors, RankIC/ICIR, hygiene gates, DSR |

### Plutchik taxonomy

Ported from `Taxonomy_Plutchik.ipynb` / Spot Runner master CSV → `data/taxonomy/plutchik_sr.csv` (56 rows; 51/56 ID overlap with Spot Runner). Closure: `sr_a_b_c → [sr_a_b_c, sr_a_b, sr_a]`.

### Fusion design

- Baseline: late fusion  
- Reference: SVC 2026 hybrid MLP-Mixer + self-attention cross-modal  
- Stretch: ImageBind-style joint embedding  
- Per-speaker longitudinal z-scores (not cross-speaker norms)

### Interpreted track — Gemini multi-sense (2026-08-10)

Hybrid **measured + interpreted** architecture:

| Track | Source | Role |
|-------|--------|------|
| **Measured** | openSMILE/librosa prosody, audEERING wav2vec2 VAD (optional), OpenFace3 / py-feat Detectorv2 | Open features with offline-safe proxies |
| **Interpreted** | Gemini video+audio (`fusion/gemini_multisense.py`) | Structured delivery / affect labels with `signal_tier: interpreted` |

**Tier A** — whole-video affect track (one pass): speaker diarization, vocal emotion, arousal/valence, delivery bands (pace / pause / pitch variability / disfluency).  
**Tier B** — per-claim clip deep pass (claim timestamp ± 15s, high-stakes / verdict-divergent only): spoken paraphrase, OCR, face/gesture description, cross-channel congruence statement (observational — not veracity).

Fusion (`align.py` + `crossmodal.py`) attaches Gemini fields onto claim rows and computes **interpreted-vs-measured agreement**; low agreement sets `modality_divergence=true` and scales the congruence score via a multiplier. Outputs remain congruence / conviction / delivery-risk only.

**Opt-in:** `MULTISENSE_ENABLED=1` → `run_multisense()` writes `{video_id}_multisense.json`, refreshes `_affect.json`, and builds `_fused_index.json`. `MULTISENSE_OFFLINE=1` forces the deterministic proxy (CI / no credentials). Trial **T007** registers interpreted–measured agreement (NO_PROMOTE until live Gemini + executive-domain audio).

Token economics (for coverage math): audio ≈ **32 tok/s**; video ≈ **258 tok/frame** at 1 FPS (see data-sourcing doc).

### Quant gates (hca-qngn)

ICIR ≥ 0.40 · frac IC+ ≥ 0.55 · weekly Jaccard < 0.25 · resid ICIR ≥ 0.5× raw · DSR ≥ 0.95 · CAR H ∈ {1,5,10,21,30}

### Compliance (sharpened)

- EU AI Act Art. 5(1)(f): biometric emotion inference prohibited in **workplace and education**; markets research is outside that prohibition.
- Explicit product clause: **not for employment, HR, or education screening**.
- Authenticity gate includes **rPPG consistency** (deepfake tell).
- No lie-detector language; vision adds congruence / arousal / delivery-risk only.

### Data sourcing

See [`docs/PREDICTIONS_DATA_SOURCING.md`](PREDICTIONS_DATA_SOURCING.md) and [`docs/H1_VENTURES_DEMO.md`](H1_VENTURES_DEMO.md).

## Output contracts

### `{video_id}_affect.json`

```json
{
  "video_id": "...",
  "schema_version": "1.0",
  "authenticity": {"pass": true, "gated": false},
  "segments": [
    {
      "claim_id": 0,
      "timestamp_sec": 81.0,
      "prosody": {"f0_mean": 120.0, "jitter": 0.01, "shimmer": 0.02, "rate_sps": 3.1},
      "disfluency": {"count": 1, "rate": 0.05},
      "exuberance": 0.42,
      "text_sentiment": 0.1
    }
  ],
  "disclaimer": "Affect features are research signals, not emotion diagnoses or veracity judgments."
}
```

### `{video_id}_multisense.json`

```json
{
  "video_id": "...",
  "schema_version": "1.0",
  "signal_tier": "interpreted",
  "tier_a": {"segments": [{"start_sec": 0, "vocal_emotion": "anticipation", "arousal": 0.5}]},
  "tier_b": [{"congruence_score": 0.6, "window": {"start_sec": 15, "end_sec": 45}}],
  "claim_delivery": [{"claim_id": 0, "tier_a": {}, "tier_b": null}],
  "disclaimer": "Interpreted multimodal delivery signals for markets research..."
}
```

Optional `Claim.delivery_signals` on report claims when the sleeve runs (`models/report.py`).

### Prediction dossier

Mirrors deepresearch naming: `{player_id}_prediction_dossier.{md,html,json}` with claims timeline, affect, congruence flags, prediction + confidence, entities, and a **Limits** section.

## Dependencies

Optional extras (see `requirements.txt` comments):

- `librosa`, `opensmile` — richer prosody (Tier-1 open)  
- Core MVP uses `numpy` + stdlib `wave` so CI can run without heavy audio stacks  
- `yfinance` — earnings calendar / surprise join (optional; fixtures ship for offline)
- Vision backends (optional): MediaPipe, OpenFace 3.0, Py-Feat Detectorv2, pyVHR — stubs fall back to synthetic
- Interpreted track (optional): `google-genai` + Vertex / API key for Gemini multi-sense; offline proxy without credentials
- Measured VAD (optional): `transformers` + audEERING wav2vec2 MSP-Podcast dimensional model; prosody proxy otherwise

## References

- Speech Craft Analytics / earnings-call vocal features literature (prior art validating thesis)  
- Spoken Alpha — per-speaker longitudinal language baselines  
- FinVoc2Vec (JAR 2026) — domain adaptation required for executive speech  
- DOLOS / DecepBench / SVC 2026 — multimodal feature families (relabeled, not shipped as deception)  
- Spot Runner Plutchik taxonomy + `sr_keywords_csv.md` story-arc schema  
- hca-qngn factor hygiene / trials ledger / DSR  
- Adapter doc pattern: `docs/marketing/closed_beta_90day/rollout/research/CLAIM_PACK_API_ONEPAGER.md`  
- Deep Research sleeve: `verityngn/services/deepresearch/`
