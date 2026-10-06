# CEO corpus sourcing — deep research

**Date:** 2026-08-14  
**Purpose:** Ranked sources of video, audio, transcripts, returns, and literature so the finance / risk-factor sleeve can leave the Karp-only n=7 seed.  
**Note:** The in-repo Deep Research pipeline (`verityngn/services/deepresearch/pipeline.py`) consumes a sanitized *video report*. It cannot research a data market. This document is the structured research pass.

**Current state:** 1 player (`ceo_pltr_karp`), 7 videos, `live_gemini: False`, T010 `n_with_car=0`. Five pilot CEOs already in `verityngn/services/players/data/pilot_ceos.json` (Cook, Nadella, Huang, Karp, Musk) — registry only.

---

## Ranked sourcing table

| Rank | Source | Modality | Coverage | Cost / license | Can we ship without it? | Notes |
|------|--------|----------|----------|----------------|-------------------------|-------|
| 1 | **YouTube / CNBC / Bloomberg public interviews** | Video + audio | Per-CEO, high variance | Free (ToS / cookies / yt-dlp) | **No** — this is the differentiator | Banker et al. template: 205 CNBC CEO interviews 2017–2019 for HFAsy |
| 2 | **Qin & Yang 2019 released corpus** | Audio + text | S&P 500 2017; 576 calls / 88,829 sentences | Academic release | **Yes for audio cold-start** | Immediate S05–S08 / S14 calibration without scraping |
| 3 | **yfinance → Sharadar / Nasdaq Data Link** | Prices / CAR | US equities | yfinance free (fragile); Sharadar paid | **No for T010+** | Today `n_with_car=0`; Sharadar is the production path per `PREDICTIONS_DATA_SOURCING.md` |
| 4 | **Quartr API** | Live + backlog audio, diarized transcripts, filings, slides | 15k+ cos, 65 markets | Enterprise | Nice-to-have for scale | Best IR data layer; SLA-documented |
| 5 | **Aiera** | Live events, transcripts, filings | Institutional | Enterprise | Nice-to-have | MCP / UI components; overlaps Quartr |
| 6 | **Refinitiv / LSEG StreetEvents** | Transcripts + some audio | Broad StreetEvents archive | Expensive terminal | Can defer | Academic precedent (Mayew / StreetEvents) |
| 7 | **EarningsCast + Seeking Alpha** | Audio + transcripts | Spotty | Free / freemium | Partial | Qin & Yang used both; alignment noisy |
| 8 | **SSRN / NBER / Chicago BFI** | Literature | Global WP | Free | **No for citations** | Not a video source; required for S00–S15 registry |
| 9 | **CRSP / Compustat / IBES** | Returns, accounting, analyst | Academic | WRDS | Defer | Needed only if we leave retail CAR |

**NSERC note:** Canadian science funding agency — not a finance-paper repository. Use **NBER** and **BFI** instead.

---

## 1. Video (the differentiator)

### What good looks like

Per player catalog (mirror `docs/karp_pre_earnings_videos.json`):

| Field | Required |
|-------|----------|
| `video_id` | Yes |
| `recorded` | Yes (ISO date) |
| `window` | `pre` / `on` / `post` |
| `next_print` | Yes for event study |
| `print_label` | Optional |
| `title` | Yes |
| `source` | YouTube (or other) URL |
| `venue` | Optional (CNBC / WEF / investor day) |
| `note` | Exclusion / context |

### Sources

| Channel | How to harvest | Risk |
|---------|----------------|------|
| CNBC YouTube / cnbc.com | Search `{CEO} {ticker} earnings` / Squawk / Closing Bell | ToS, SABR/yt-dlp blocks → cookies + android client |
| Bloomberg YouTube | Same pattern | Often geo / clip-length limited |
| Yahoo Finance | Interview uploads | Lower density |
| WEF / conference channels | Prepared long-form (Venue B class) | Venue prior matters — keep labeled |
| Company IR / investor day | Webcasts | Prefer downloadable MP4; avoid print-day for T010-style tests |

### Academic sample-construction precedent

**Banker et al., Management Science 70(7) 2024** — scraped **205 CEO video interviews on CNBC about corporate earnings (2017–2019)**, CNN face detect, hemifacial asymmetry (HFAsy). Negative CAR, wider bid-ask, lower analyst revisions. **This is the template for our multi-CEO video catalog builder.**

Also: Blankespoor et al. SSRN 4598747 (expression–news incongruence → analyst dispersion); Dai/Huang/Li SSRN 4720163 (DHFA → audit fees).

### Pilot expansion order

1. **Huang / NVDA** — dense CNBC + GTC keynotes; next catalog after Karp  
2. **Cook / AAPL** — more prepared venues; good Venue B contrast  
3. **Nadella / MSFT** — similar  
4. **Musk / TSLA** — mediasphere velocity stress test; untradable entities stay mediasphere-only  

Target: ≥5 pre-print videos per player before any multi-CEO promote discussion.

---

## 2. Audio + transcripts at scale

| Vendor | Strength | Weakness | When to buy |
|--------|----------|----------|-------------|
| **Quartr** | Global live + backlog MPEG audio, speaker-ID transcripts, filings, slides; modular REST; SLAs | Paid | When we leave YouTube-only and need earnings-call audio at S&P scale |
| **Aiera** | Live IR events + AI tools | Paid; overlap | Alternative / complement to Quartr |
| **StreetEvents (LSEG)** | Canonical academic archive | Terminal pricing | Only with WRDS / campus access |
| **EarningsCast** | Downloadable call audio | Alignment noisy | Cheap bootstrap |
| **Seeking Alpha** | Transcripts | No reliable audio | Text lane only |

**Immediate free path:** Qin & Yang 2019 released S&P 500 2017 earnings-call audio+text (576 aligned calls). Use for S05–S08 / S14 method checks before paying for Quartr.

---

## 3. Outcomes / returns

| Source | Status | Action |
|--------|--------|--------|
| **yfinance** | Wired in `scripts/karp_earnings_effect.py`; currently returns `None` → `n_with_car=0` | Fix env + download robustness (T010 unblock) |
| **Sharadar / Nasdaq Data Link** | Named in `PREDICTIONS_DATA_SOURCING.md` | Production CAR / FF-adj path |
| **CRSP / Compustat / IBES** | Academic | Only if WRDS available |

Hygiene: features as-of video date *t* only; pre-print interviews only for earnings tests; register trial before peeking CAR.

---

## 4. Literature repositories

| Repo | Use |
|------|-----|
| **SSRN** | Working papers (Blankespoor, Kim/Muhn/Nikolaev FSA caveat) |
| **NBER** | Macro / asset-pricing WPs |
| **Chicago BFI** | Koijen–Levy Explaining Markets; Kim–Muhn–Nikolaev risk paper |
| **arXiv** | Vision / AU / derailment methods |
| **ACL Anthology** | Qin & Yang 2019 MDRM |

---

## 5. Recommended 90-day sourcing sequence

1. **Week 0–1:** Fix yfinance CAR join; re-run T010.  
2. **Week 1–2:** Huang/NVDA pre-earnings catalog (≥5 videos); generalize build scripts.  
3. **Week 2–4:** Qin & Yang audio cold-start for measured-track calibration (S02/S07/S08).  
4. **Week 4–8:** CNBC scrape pass for Cook + Nadella (Banker-style).  
5. **Week 8–12:** Evaluate Quartr pilot quote; decide vs staying YouTube+Qin.  
6. **Ongoing:** Register Explaining Markets SDK as text-lane external scorecard (see companion doc).

---

## What “enough” means before promote

| Gate | Threshold |
|------|-----------|
| Videos / player | ≥5 with live Gemini Tier A (not only offline_proxy) |
| Players | ≥3 with catalogs |
| CAR join | `n_with_car` ≥ 10 events, leakage-safe |
| Hygiene | ICIR ≥ 0.40, DSR ≥ 0.95, etc. (`docs/trials_ledger.md`) |
| Language | Risk-factor only; **NO_PROMOTE** until gates pass |

Until then the panel is an **instrumentation / risk-measurement proof**, not a tradable factor.
