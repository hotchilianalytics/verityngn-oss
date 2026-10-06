# VerityIndex Predictions — Data Sourcing Spec

**Date:** 2026-08-06  
**Purpose:** What we must collect to (a) run an internal alt-data fund sleeve and (b) sell a licensed feed to hedge funds.

## 1. Audio + transcripts (earnings calls)

| Vendor | Coverage | What we need | Notes |
|--------|----------|--------------|-------|
| **Quartr API** | 15k+ companies, 65 markets | Live + backlog audio, speaker-ID transcripts, event IDs | Best primary for global IR events |
| **EQL API** | 35k companies, 89 countries | JSON within ~60s of publish | Broad coverage / fast drop |
| **Benzinga conference-call API** | US-heavy | HLS live + MP3 archive + speaker structs | Good for live streaming ingest |
| **earningscalls.dev** | 247k transcripts, 12k cos | Cheap backfill tier | Cost control for historical panel |

**Minimum fields per call:** `company_id`, `ticker`, `event_ts`, `audio_url`, `transcript_segments[{speaker, role, t_start, t_end, text}]`, `call_type` (earnings|CMD|AGM|other).

## 2. Video — the real bottleneck

Most earnings calls are **audio-only**. Vision/spectral features need a separate **video-event universe**:

| Source class | Examples | Vision value | Licensing risk |
|--------------|----------|--------------|----------------|
| Keynotes | GTC, WWDC, Build, Demo Day | High (face + slides) | Official streams preferred |
| Broadcast interviews | CNBC, Bloomberg | High | Clip licensing / fair use limits |
| Conference firesides | Davos, StrictlyVC, All-In | High (Karp/Musk dense) | Event ToS |
| Shareholder meetings | Annual meetings | Medium | Often restricted |
| Depositions / testimony | Court / Congress | High stress signal | Public record when available |
| YouTube reuploads | Fan / channel mirrors | Convenient but fragile | **YouTube ToS** — follow existing VerityIndex compliance position; prefer first-party IR |

**Rule:** attribute each video to `player_id` + optional `entity` (for Musk: TSLA vs xAI vs SpaceX vs X). Untradable entities never become prediction targets.

## 3. Ground truth labels

| Label family | Source | Use |
|--------------|--------|-----|
| EPS actual / estimate / surprise | Sharadar / Nasdaq Data Link; yfinance fallback | Primary target |
| Guidance change | 8-K Item 2.02 / 8.01 | Spoken Alpha-style confirmation |
| Clean miss | Next-quarter actual vs Street | Lagged validation |
| Trailing pre-announce | Item 8.01 | Confirmation family |
| Forward returns / CAR | Prices vendor (Sharadar SEP or equivalent) | H = 1/5/10/21/30 event study |

## 4. Point-in-time (PIT) discipline

Every feature row must carry:

| Stamp | Meaning |
|-------|---------|
| `event_ts` | When the speech/video happened |
| `media_publish_ts` | When media became public |
| `processing_completed_ts` | When *our* pipeline finished |
| `asof_available` | **Earliest** time a trader could have the feature (= `processing_completed_ts`) |

**Usable only when `asof_available <= trade_date`.** Join with `merge_asof(direction="backward")` — **no bfill**. Never `fillna(0)` on sparse coverage (collapses cross-sectional ranks).

## 5. Coverage & cost envelope (500-name universe)

Assumptions:

- 500 tickers × 4 earnings calls/yr = **2,000 calls/yr**
- + ~2 video events/CEO/yr for top 100 names = **~200 vision-heavy events/yr**
- Audio processing: ~$0.01–0.05 / min (STT + prosody) → order **$5–25k/yr** at scale depending on vendor
- Vision (OpenFace/rPPG on keynotes): GPU minutes dominate — budget **1–2× audio** for the video subset
- **Gemini multi-sense (interpreted track):**
  - Audio understanding ≈ **32 tokens / second** of audio (~1,920 tok/min)
  - Video ≈ **258 tokens / frame** at 1 FPS (plus audio tokens when both streams are sent)
  - Tier A = 1 whole-video pass; Tier B = clipped windows only (claim ±15s, high-stakes subset) to bound cost
  - Rough envelope for 200 vision-heavy events/yr at ~20 min + 5 Tier-B clips × 30s: order **tens of millions of tokens/yr** — price against Vertex Gemini Flash; keep `MULTISENSE_OFFLINE` for CI
- Transcript backfill (5y × 500 names): prefer earningscalls.dev / Quartr backlog, not DIY scrape

Storage: raw audio ~50–200 MB/call; vision frames at 5 fps downscaled ≪ raw 1080p. Keep derived features (JSONL) as the durable store; raw media is hot-cache.

## 6. Two revenue paths

### A. Internal fund sleeve

- Media factors → `build_media_factors.py` → hygiene gates → event-study CAR → optional Broad80-style book
- Promote only after `factor_hygiene_pass` **and** portfolio gates (hca-qngn doctrine)
- Operational α bar: **+2%/yr** residual vs SPY research gate (not the aspirational 50% note)

### B. Licensed feed to hedge funds

Institutional behavioral-data feeds in this category price roughly **$10k–$100k / month**. Proposed tiers:

| Tier | Contents | Compliance clause |
|------|----------|-------------------|
| **Scores** | Congruence, conviction, delivery-risk bands, mediasphere velocity | Markets research only; not HR/education |
| **Features** | Tier-1 prosody + vision summaries + Plutchik `sr_*` timed segments | Same + authenticity gate flags |
| **Raw fused index** | Full `full_index` / `story_arcs` / modality contributions | Same + no lie-detector warranty |

## 7. Competitor landscape (validates demand)

- **Speech Craft Analytics** — vocal alpha; `nervous_mgmt` 0.28–0.61% excess H=5..30
- **Spoken Alpha** — per-speaker longitudinal language baselines (hedge density, Q&A evasion)
- **FinVoc2Vec (JAR 2026)** — actor-trained vocal tone → **chance** on real calls; domain adaptation required
- Our wedge: **vision + spectral + claims verification** fused — not text-or-voice alone

## 8. Immediate acquisition checklist

1. Pick transcript+audio primary (Quartr or EQL) + cheap backfill  
2. Build 5-CEO video seed set (Cook, Nadella, Huang, Karp, Musk) with entity tags  
3. Wire Sharadar (or equivalent) EPS + prices for CAR  
4. Register trials T002–T007 **before** computing hold-out metrics  
5. Legal review of YouTube / broadcast clip use for commercial feed
6. Decide Gemini live vs offline for H1 demo; never promote T007 offline proxy scores
