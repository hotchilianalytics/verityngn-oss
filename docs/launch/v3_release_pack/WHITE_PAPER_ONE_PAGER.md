# Claim-level risk abatement — one-pager

**VerityNgn OSS 3.0.1** · Apache-2.0 engine · HotChili Analytics · Launch **Monday Nov 16, 2026**  
**PyPI:** `pip install 'verityngn[deep]==3.0.1'` · engine tip `1b2cca8` · Primary-10 battery **PASS** · Examples: [`../EXAMPLES.md`](../EXAMPLES.md) · Multimodal brief: [`MULTIMODAL_AND_FUTURES_v3.md`](MULTIMODAL_AND_FUTURES_v3.md)

## Problem

Marketing, legal, agency, and **analyst-creator** teams need **claim-level** disclosure and brand-safety review on video — not a single “truth score” or lie detector. Securities counsel needs the same pattern on **own-record** hedges (Item 1A vs 8-K).

## What VerityNgn is now

A **risk platform** layered on an open engine:

1. **Extract** claims from multimodal video (adaptive **1–6 fps**, speech, OCR, charts, exhibits) — or filings for disclosure. **81** pixel-only claims across 10 v3 release runs (69 in the final primary-10); **18/40 (45%)** on SB1507; silent Lipozem credential cards.
2. **Classify** into six kinds (source-backed fact, data-derived inference, causal/analytical, reasoned opinion, prediction, unverified assertion).
3. **Verify** with counter-intelligence; stamp likelihood, evidence confidence, residual reliance risk.
4. **Report** — consumer: TRUE/FALSE ladder + CRAAP. Analyst: typed sections + risk chips + SIFT. Disclosure: Rewrite / Keep / Move / Remove. Auto-emit `brand_safety_scores.json` + `{id}_exhibit_map.json`.
5. **Optional Deep Research** — grounded forensic risk brief with `visual_only_claims` lead + citation audit trail.

**Roadmap:** 3.1 object/action semantics + visual–spoken contradiction · 3.2 pose/lip/audio congruence (opt-in sleeves already in the wheel).

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
- SB1507 report is public (Chris approved); the source mp4 stays local and out of git
- No crawl / surveil product (disclosure uses public EDGAR + optional client vault)

## Open-core boundary

Engine quality + research sleeves (including **predictions / RiskFactor sensors S00–S15**) live in **verityngn-oss** (Apache). Hosted control plane, trial credits, gallery scale, and ClearFactor **services** (vault, counsel briefs) sit on **verityindex.com**. Disclosure **engine** opens as `verityngn[disclosure]` (Phase 1). See [COMMERCIAL_MAP.md](../../platform/COMMERCIAL_MAP.md) and [OPEN_CORE.md](../../OPEN_CORE.md).

## Proof

- Primary-10 battery: [BATTERY_RESULTS_v3.md](../BATTERY_RESULTS_v3.md)
- Matrix: [RELEASE_TEST_MATRIX_v3.md](../RELEASE_TEST_MATRIX_v3.md)

## Contact

- Install: `pip install 'verityngn[deep]==3.0.1'` · https://pypi.org/project/verityngn/3.0.1/  
- Gallery: https://verityindex.com/gallery  
- Engine: https://github.com/hotchilianalytics/verityngn-oss  
- Series: `docs/blog/series/`  
- Platform: `docs/platform/`
