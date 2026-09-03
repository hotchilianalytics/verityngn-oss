# VerityNgn OSS v3.0.0 Release Notes

Standalone Apache-2.0 multimodal video claim verification engine with Deep Research.

## Highlights

- **Analysis tiers**: `light` (VTT + DR-direct), `full` (pipeline + optional DR), `auto` (sufficiency routing), `local-light`, `local-full`
- **Unified captions**: `verityngn captions <url>` — cached VTT → yt-dlp → transcript API → **Supadata** / Groq ASR (opt-in) → Gemini `.gemini.vtt` fallback
- **T-ABL-005:** VTT→DR ~15s vs JSON→DR ~20s (40 claims); Jaccard 0.22 → full pipeline default
- Deep Research (`verityngn analyze --deep`) in OSS
- Adaptive vision sleeve: genre FPS, exhibit maps, brand-safety visual flags, Modality column
- Authenticity gate stubs + spectral AI-voice cues + MediaPipe Face Landmarker
- Open-core docs: `docs/OPEN_CORE.md`, `docs/DEPENDENCY_MODEL.md`
- Boundary CI scrub (no predictions/quant in package)
- Release paper + charts: `papers/verityngn_oss_v3_release.{md,pdf}`

## Install

```bash
pip install 'verityngn==3.0.0'
# from source: pip install -e '.[deep,vision,audio]'
verityngn analyze --tier auto '<url>'
verityngn analyze --tier light '<url>'
verityngn analyze --tier full '<url>' --deep
verityngn captions '<url>'
```

## Environment

| Variable | Purpose |
|----------|---------|
| `VERITY_GEMINI_KEY` | Gemini Developer API for analysis + DR |
| `YTDLP_COOKIES` | Path to cookies.txt for YouTube captions |
| `SUPADATA_API_KEY` | Opt-in paid native/generate captions |
| `GROQ_API_KEY` | Opt-in Whisper ASR last resort |
| `TRANSCRIPT_MAX_COST_USD` | Paid transcript spend guard (default 0.05) |
| `YOUTUBE_API_KEY` | Optional metadata only (not caption download) |
| `SKIP_LIVE_CAPTION_FETCH=1` | Cache-only captions (CI) |

## Docker

```bash
docker build -f Dockerfile.api -t verityngn-oss:v3.0.0 .
docker build -f Dockerfile.batch -t verityngn-oss-batch:v3.0.0 .
```

## Not included

Predictions, RiskFactor S00–S15, hosted trial/credits SaaS.

## Artifacts

- PDF: `papers/verityngn_oss_v3_release.pdf`
- Caption guide: `docs/guides/YOUTUBE_CAPTIONS.md`
- Media pack: `docs/launch/v3_release_pack/MEDIA_CHECKLIST.md`
- Parity checklist: `PARITY_TEST_v3.md`
