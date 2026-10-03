# Blog post — VerityNgn OSS 3.0.0

**Title:** VerityNgn 3.0: open-source video claim-risk analysis, Deep Research, and analyst-genre reports  
**CTA:** GitHub `release/v3.0.0` · gallery proof · blog series in `docs/blog/series/`  
**Candidate SHA:** `5258292` (tag moves only after [`RELEASE_TEST_MATRIX_v3.md`](../RELEASE_TEST_MATRIX_v3.md) is green)

## Lead

**VerityNgn OSS 3.0.0** is a standalone multimodal engine for extracting and verifying claims from video. This candidate adds **Deep Research** in the Apache tree, analysis tiers, and a new **analyst-video grammar**: six claim kinds, dual risk metrics (likelihood · evidence confidence · residual reliance risk), and a SIFT method review in place of CRAAP when the video is deep-data analysis.

## Four analysis tiers

| Tier | Command | What you get |
|------|---------|--------------|
| **light** | `verityngn analyze --tier light <url>` | Captions → DR-direct risk brief |
| **full** | `verityngn analyze --tier full <url> --deep` | Full pipeline + Deep Research |
| **local-light** | `verityngn analyze --tier local-light -f clip.mp4` | File transcript → DR-direct |
| **local-full** | `verityngn analyze --tier local-full -f clip.mp4` | Full report on upload (analyst genre when claim mix warrants) |

## Claim kinds and genre-aware §9

Consumer / promotional videos stay on the classic TRUE/FALSE ladder with **CRAAP** in section 9.

Analyst videos (method, $, %, causal legislative logic) route into typed sections with **risk chips**, and section 9 becomes **Method & Reliance Review (SIFT)**. Academic-cite density is not the primary evidence bar for that genre.

See series parts 2–4 and charts under `docs/blog/series/assets/`.

## Two demos

| Video | Shows |
|-------|-------|
| Lipozem `tLJC8hkK-ao` (public) | Old ladder, CRAAP, Deep Research |
| SB1507 local (Chris; full report gated) | New lanes, SIFT, risk chips. Publish aggregate charts only until approved. |

## Caption operator tip

YouTube Data API metadata does **not** download `.en.vtt` for arbitrary public videos.

```bash
verityngn captions 'https://www.youtube.com/watch?v=VIDEO_ID'
```

## Why open the engine

Open-core only works if the free engine is impressive. Predictions and RiskFactor stay closed overlays that pin OSS ≥3.0.0.

## Quickstart

```bash
pip install -e '.[deep]'   # from release/v3.0.0 until retag/PyPI
verityngn analyze --tier full 'https://www.youtube.com/watch?v=tLJC8hkK-ao' --deep
```

## Honest locks

- Not a lie detector / not earnings prediction
- Lipozem-class VSL = weak multimodal proof
- One primary link per post; stagger Reddit / HN / X
