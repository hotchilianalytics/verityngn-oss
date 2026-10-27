# VerityNgn OSS v3.0.0 Release Notes

Standalone Apache-2.0 multimodal **claim-risk** engine with Deep Research — the L1 core of the VerityNgn risk platform.

## Release candidate

| Field | Value |
|-------|-------|
| Branch | `release/v3.0.0` |
| Package version | **3.0.0** (`pyproject.toml`) |
| Battery SHA | `b13bcf1` (primary-10 PASS) |
| Engine/Batch pin | `94f62f6` |
| Git tag `v3.0.0` | Operator go 2026-10-26 — moves to this release tip |
| Test matrix | [`docs/launch/RELEASE_TEST_MATRIX_v3.md`](RELEASE_TEST_MATRIX_v3.md) |
| Battery | [`docs/launch/BATTERY_RESULTS_v3.md`](BATTERY_RESULTS_v3.md) |
| Platform | [`docs/platform/PLATFORM_OVERVIEW.md`](../platform/PLATFORM_OVERVIEW.md) |

## Highlights

- **Analysis tiers**: `light`, `full`, `auto`, `local-light`, `local-full`
- **Unified captions**: `verityngn captions <url>`
- Deep Research (`verityngn analyze --deep`) in OSS
- Adaptive vision sleeve: genre FPS, exhibit maps, brand-safety visual flags
- Authenticity gate stubs + spectral AI-voice cues + MediaPipe Face Landmarker
- **Analyst claim taxonomy:** six kinds with dual metrics and risk chips
- **Genre-aware §9:** CRAAP (consumer) vs SIFT (analyst)
- **Predictions / RiskFactor sensors (S00–S15)** absorbed into OSS (`verityngn[predictions]`)
- Primary-10 live battery **PASS** (Huang Squawk swap documented)
- Platform morph docs: report → layered risk platform
- Open-core: `docs/OPEN_CORE.md`, `docs/DEPENDENCY_MODEL.md`

## Install

```bash
pip install 'verityngn==3.0.0'
# from source until then:
pip install -e '.[deep,vision,audio]'
# optional research sleeve:
pip install -e '.[predictions]'
verityngn analyze --tier auto '<url>'
verityngn analyze --tier full '<url>' --deep
verityngn captions '<url>'
```

## Environment

| Variable | Purpose |
|----------|---------|
| `VERITY_GEMINI_KEY` / Vertex ADC | Gemini for analysis + DR |
| `VERTEX_LOCATION=global` | Required for current Vertex models |
| `YTDLP_COOKIES` | Path to cookies.txt for YouTube captions |
| `SUPADATA_API_KEY` | Opt-in paid native/generate captions |
| `GROQ_API_KEY` | Opt-in Whisper ASR last resort |
| `YOUTUBE_API_KEY` | Optional metadata only (not caption download) |

## Docker

```bash
docker build -f Dockerfile.api -t verityngn-oss:v3.0.0 .
docker build -f Dockerfile.batch -t verityngn-oss-batch:v3.0.0 .
```

## Open vs hosted

| In OSS | Hosted / paid (verityindex.com, ClearFactor) |
|--------|-----------------------------------------------|
| Engine, DR, CI, predictions sensors | Multi-tenant API, credits, Stripe |
| Domain pack logic | Control plane / gallery scale |
| Disclosure engine (Phase 1 sleeve) | Vault, counsel briefs, quarterly ops |

## Artifacts

- PDF: `papers/verityngn_oss_v3_release.pdf`
- Platform figure: `papers/figures/platform_layers.png`
- Media pack: `docs/launch/v3_release_pack/MEDIA_CHECKLIST.md`
- Exec summary: `docs/launch/EXEC_SUMMARY_v3.md`
