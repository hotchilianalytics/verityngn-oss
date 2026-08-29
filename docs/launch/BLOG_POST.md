# Blog post — VerityNgn OSS 3.0.0

**Title:** VerityNgn 3.0: Drop-in open-source video verification with Deep Research  
**CTA:** `pip install verityngn` · GitHub · Streamlit demo · release paper

## Lead

Today we publish **VerityNgn OSS 3.0.0** — a standalone multimodal engine for extracting and verifying claims from video. The headline change: **Deep Research** (our grounded forensic pass) ships in the Apache tree alongside the standard report CLI.

## Why open the engine

Open-core only works if the free engine is impressive. We moved engine-quality Deep Research, authenticity stubs, spectral voice cues, and a MediaPipe Face Landmarker adapter into OSS, and documented that commercial SaaS, predictions, and RiskFactor products build **on top of** this base.

## Quickstart

```bash
pip install 'verityngn[deep]'
verityngn analyze 'https://www.youtube.com/watch?v=VIDEO_ID' --deep
```

## What we are not shipping

No Karp earnings panels, no RiskFactor S00–S15 registry, no lie-detector claims. Those remain closed overlays or out of scope.

## Artifacts

- Release paper with charts: `papers/verityngn_oss_v3_release.md`
- Open-core boundary: `docs/OPEN_CORE.md`
- CHANGELOG `[3.0.0]`

## Links

- GitHub: https://github.com/hotchilianalytics/verityngn-oss  
- Demo: https://verityngn.streamlit.app  
- Licensing: Apache-2.0 + commercial addendum for hosted offerings  
