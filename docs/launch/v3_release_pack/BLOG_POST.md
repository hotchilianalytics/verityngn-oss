# Blog post — VerityNgn OSS 3.0.0

**Title:** VerityNgn 3.0: Drop-in open-source video verification with Deep Research  
**CTA:** `pip install verityngn` · GitHub · Streamlit demo · release paper

## Lead

Today we publish **VerityNgn OSS 3.0.0** — a standalone multimodal engine for extracting and verifying claims from video. The headline change: **Deep Research** (our grounded forensic pass) ships in the Apache tree alongside the standard report CLI.

## Four analysis tiers

| Tier | Command | What you get |
|------|---------|--------------|
| **light** | `verityngn analyze --tier light <url>` | Captions → DR-direct risk brief (~60s) |
| **full** | `verityngn analyze --tier full <url> --deep` | Full pipeline + optional Deep Research |
| **local-light** | `verityngn analyze --tier local-light -f clip.mp4` | File transcript → DR-direct |
| **local-full** | `verityngn analyze --tier local-full -f clip.mp4 --deep` | Full report on upload |

## Caption operator tip

YouTube Data API metadata does **not** download `.en.vtt` for arbitrary public videos. PoToken rollout breaks `youtube_transcript_api` (empty HTTP 200). Use fresh browser cookies, then Gemini fallback if needed:

```bash
verityngn captions 'https://www.youtube.com/watch?v=VIDEO_ID'
# fallback writes VIDEO_ID.gemini.vtt (synthetic — not official captions)
```

**Ablation (T-ABL-005):** `--tier light` (VTT→DR, ~15s) vs `--tier full --deep` (40-claim JSON→DR, ~20s DR only). Light is triage; full is audit default (Jaccard 0.22 between DR outputs on Lipozem seed).

## Why open the engine

Open-core only works if the free engine is impressive. We moved engine-quality Deep Research, authenticity stubs, spectral voice cues, adaptive vision sampling, and a MediaPipe Face Landmarker adapter into OSS, and documented that commercial SaaS, predictions, and RiskFactor products build **on top of** this base.

## Quickstart

```bash
pip install 'verityngn[deep]'
verityngn analyze --tier light 'https://www.youtube.com/watch?v=VIDEO_ID'
verityngn analyze --tier full 'https://www.youtube.com/watch?v=VIDEO_ID' --deep
```

## What we are not shipping

No Karp earnings panels, no RiskFactor S00–S15 registry, no lie-detector claims. Those remain closed overlays or out of scope.

## Artifacts

- Release paper with charts: `papers/verityngn_oss_v3_release.md`
- Media checklist: `docs/launch/v3_release_pack/MEDIA_CHECKLIST.md`
- Open-core boundary: `docs/OPEN_CORE.md`
- CHANGELOG `[3.0.0]`

## Links

- GitHub: https://github.com/hotchilianalytics/verityngn-oss  
- Demo: https://verityngn.streamlit.app  
- Licensing: Apache-2.0 + commercial addendum for hosted offerings  
