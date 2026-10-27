# Claim-level risk abatement — one-pager

**VerityNgn OSS 3.0.0 candidate** · Apache-2.0 engine · HotChili Analytics  
**SHA:** `b13bcf1` on `release/v3.0.0` · Primary-10 battery **PASS**

## Problem

Marketing, legal, agency, and **analyst-creator** teams need **claim-level** disclosure and brand-safety review on video — not a single “truth score” or lie detector. Securities counsel needs the same pattern on **own-record** hedges (Item 1A vs 8-K).

## What VerityNgn is now

A **risk platform** layered on an open engine:

1. **Extract** claims from multimodal video (speech, on-screen text, charts) — or filings for disclosure.
2. **Classify** into six kinds (source-backed fact, data-derived inference, causal/analytical, reasoned opinion, prediction, unverified assertion).
3. **Verify** with counter-intelligence; stamp likelihood, evidence confidence, residual reliance risk.
4. **Report** — consumer: TRUE/FALSE ladder + CRAAP. Analyst: typed sections + risk chips + SIFT. Disclosure: Rewrite / Keep / Move / Remove.
5. **Optional Deep Research** — grounded forensic risk brief with citation audit trail.

Platform layers: [docs/platform/PLATFORM_OVERVIEW.md](../../platform/PLATFORM_OVERVIEW.md).

## Analysis tiers

| Tier | Best for | Output |
|------|----------|--------|
| **light** | Fast YouTube triage | VTT/Gemini → DR-direct |
| **full** | Diligence / gallery | Claim report + DR |
| **local-light** | Clip triage | DR on file transcript |
| **local-full** | Matter / analyst upload | Full report; genre-aware §9 |

## Domain packs (samples)

Consumer CRAAP · Analyst SIFT · CEO predictions sensors · Securities disclosure (rfkit / ClearFactor) · Legal deposition · Health CI · Brand safety — see [DOMAIN_PACKS.md](../../platform/DOMAIN_PACKS.md).

## What we do not claim

- Not earnings prediction or allocation alpha
- Not a lie detector or moral truthfulness score
- YouTube API key ≠ caption download for arbitrary public videos
- SB1507 full report stays private until the creator approves excerpts
- No crawl / surveil product (disclosure uses public EDGAR + optional client vault)

## Open-core boundary

Engine quality + research sleeves (including **predictions / RiskFactor sensors S00–S15**) live in **verityngn-oss** (Apache). Hosted control plane, trial credits, gallery scale, and ClearFactor **services** (vault, counsel briefs) sit on **verityindex.com**. Disclosure **engine** opens as `verityngn[disclosure]` (Phase 1). See [COMMERCIAL_MAP.md](../../platform/COMMERCIAL_MAP.md) and [OPEN_CORE.md](../../OPEN_CORE.md).

## Proof

- Primary-10 battery: [BATTERY_RESULTS_v3.md](../BATTERY_RESULTS_v3.md)
- Matrix: [RELEASE_TEST_MATRIX_v3.md](../RELEASE_TEST_MATRIX_v3.md)

## Contact

- Gallery: https://verityindex.com/gallery  
- Engine: https://github.com/hotchilianalytics/verityngn-oss  
- Series: `docs/blog/series/`  
- Platform: `docs/platform/`
