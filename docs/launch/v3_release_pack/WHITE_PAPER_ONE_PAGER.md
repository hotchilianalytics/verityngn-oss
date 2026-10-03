# Claim-level risk abatement — one-pager

**VerityNgn OSS 3.0.0 candidate** · Apache-2.0 engine · HotChili Analytics  
**SHA:** `5258292` on `release/v3.0.0`

## Problem

Marketing, legal, agency, and **analyst-creator** teams need **claim-level** disclosure and brand-safety review on video — not a single “truth score” or lie detector.

## What VerityNgn does

1. **Extract** claims from multimodal video (speech, on-screen text, charts).
2. **Classify** into six kinds (source-backed fact, data-derived inference, causal/analytical, reasoned opinion, prediction, unverified assertion).
3. **Verify** with counter-intelligence search; stamp likelihood, evidence confidence, residual reliance risk.
4. **Report** — consumer videos: TRUE/FALSE ladder + CRAAP. Analyst videos: typed sections + risk chips + SIFT method review.
5. **Optional Deep Research** — grounded forensic risk brief with citation audit trail.

## Analysis tiers

| Tier | Best for | Output |
|------|----------|--------|
| **light** | Fast YouTube triage | VTT/Gemini → DR-direct |
| **full** | Diligence / gallery | Claim report + DR |
| **local-light** | Clip triage | DR on file transcript |
| **local-full** | Matter / analyst upload | Full report; genre-aware §9 |

## What we do not claim

- Not earnings prediction or allocation alpha
- Not a lie detector or moral truthfulness score
- YouTube API key ≠ caption download for arbitrary public videos
- SB1507 full report stays private until the creator approves excerpts

## Open-core boundary

Engine quality lives in **verityngn-oss** (Apache). Hosted API, trial credits, legal dossier packaging, and RiskFactor registry are **closed overlays** that pin OSS ≥3.0.0.

## Contact

- Gallery: https://verityindex.com/gallery  
- Engine: https://github.com/hotchilianalytics/verityngn-oss  
- Series: `docs/blog/series/`  
- Matrix: `docs/launch/RELEASE_TEST_MATRIX_v3.md`
