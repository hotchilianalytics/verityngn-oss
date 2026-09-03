# Claim-level risk abatement — one-pager

**VerityNgn OSS 3.0+** · Apache-2.0 engine · HotChili Analytics

## Problem

Marketing, legal, and agency teams need **claim-level** disclosure and brand-safety review on video — not a single “truth score” or lie detector.

## What VerityNgn does

1. **Extract** factual claims from multimodal video (speech, on-screen text, charts).
2. **Verify** each claim with counter-intelligence search and source reputation scoring.
3. **Report** TRUE / FALSE / UNCERTAIN with calibrated confidence and CRAAP analysis.
4. **Optional Deep Research** — grounded forensic risk brief with citation audit trail.

## Analysis tiers

| Tier | Best for | Output |
|------|----------|--------|
| **light** | Fast YouTube triage | VTT/Gemini → DR-direct (~15s on seed) |
| **full** | Diligence / gallery | 40-claim report + DR (~20s DR pass) |
| **local-light** | Deposition clip triage | DR on file transcript |
| **local-full** | Matter dossier | Full report on upload |

## What we do not claim

- Not earnings prediction or allocation alpha
- Not a lie detector or moral truthfulness score
- YouTube API key ≠ caption download for arbitrary public videos

## Open-core boundary

Engine quality lives in **verityngn-oss** (Apache). Hosted API, trial credits, legal dossier packaging, and RiskFactor registry are **closed overlays** that pin OSS ≥3.0.0.

## Contact

- Gallery: https://verityindex.com/gallery  
- Engine: https://github.com/hotchilianalytics/verityngn-oss  
- Docs: `docs/OPEN_CORE.md`
