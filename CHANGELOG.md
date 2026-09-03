# Changelog

All notable changes to VerityNgn will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-09-03

Candidate cut on `release/v3.0.0` (intended to replace `main` after operator testing). Existing git tag `v3.0.0` still points at the 2026-08-29 canonical engine commit until retag is approved.

### Added
- **`--tier auto`**: preflight sufficiency routing (coverage / visual density / duration) with quality-floor escalation
- **Paid transcript adapters**: Supadata (native, 202/jobId poll) + Groq ASR last resort; `{id}.vendor.vtt` never clobbers `.en.vtt`
- **Sufficiency metrics** (`risk_recall@K`, cost/latency `arm_cost.json`); untruncated light-arm transcript
- **Archive paper**: `papers/verityngn_v3_ablation_archive.{md,pdf}` (T-ABL-006/007, T-TX-002)
- **Analysis tiers** (`--tier light|full|auto|local-light|local-full`): light = VTT + DR-direct; full = pipeline + optional DR
- **Unified caption fetch** (`services/video/caption_fetch.py`): cached VTT → yt-dlp android+cookies → transcript API → paid vendors → Gemini
- **CLI `verityngn captions`**: subs-only operator debugging (no LLM)
- **Tier router** (`services/tiers/router.py`) dispatching light/full/local paths
- **Gemini YouTube URL caption fallback** (`CAPTION_GEMINI_FALLBACK`): writes `.gemini.vtt` when scrapers fail (synthetic, not official captions)
- **T-ABL-005 ablation** script: VTT→DR vs report-JSON→DR (`scripts/run_vtt_json_dr_ablation.py`)
- **Deep Research in OSS**: full `client` / `pipeline` / `renderer` + `dr_prompt_v1` (previously commercial-only)
- **CLI `--deep` / `--deep-only`**: grounded forensic / risk brief after standard report
- **CLI `local analyze` / `ablate`**: local mp4/URL testing + DR-direct ablation
- **Ablation module** (`services/ablation/`): full pipeline vs DR-direct without claims inventory
- **Authenticity gate** + stub adapters (C2PA / Corsound / visual) for optional media provenance
- **Spectral AI-voice cues** (`services/video/ai_detection.py`, optional `librosa`)
- **MediaPipe Face Landmarker** + story-arc continuity stub (`services/vision/`)
- **Display labels** for risk abatement framing (internal TRUE/FALSE/UNCERTAIN unchanged)
- **Open-core docs**: `docs/OPEN_CORE.md`, `docs/DEPENDENCY_MODEL.md`, Gemini capability gap memo
- **Boundary tests**: fail CI if predictions/quant/Karp paths appear under `verityngn/`
- **Release paper refresh** for v3 public announcement

### Changed
- Package version reconciled to **3.0.0** (was pyproject `0.3.0` vs historic tags)
- Open-core boundary: Deep Research is OSS; predictions and riskfactor stay closed overlays
- User-facing narrative: **claim-level risk abatement** (not “truthfulness” / lie detector)
- Commercial/predictions/riskfactor expected to **depend on OSS ≥3.0.0**

### Security
- Tightened `.gitignore` for analysis dumps and local noise
- SECURITY.md supported versions updated for 3.0.x

## [2.1.0] - 2025-11-12

### Added
- **Workflow Logging System**: Comprehensive debug-level logging saved to `.log` files in outputs directory
- **Streamlit Community Cloud Deployment**: API-first architecture enabling cloud-hosted UI
- **Migration Script**: Automated script for file restructuring (`scripts/migrate_to_milestone.sh`)
- **Test Directory Structure**: Organized test files into `test/{unit,integration,debug,scripts,utils}/`
- **Documentation Organization**: Moved development notes to `docs/cursor_dev/` and deployment guides to `docs/deployment/`

### Changed
- **File Structure**: Major reorganization of test files and documentation
  - Test files moved from root to `test/` directory
  - Development notes moved to `docs/cursor_dev/`
  - Deployment guides moved to `docs/deployment/`
- **API Polling**: Reduced polling frequency from 2s to 5-15s with exponential backoff
- **Error Handling**: Enhanced permission error handling for cloud environments
- **Gallery Component**: Added default values for missing fields to prevent KeyErrors

### Fixed
- **Gallery KeyError**: Fixed missing `youtube_url` and `submitted_at` field errors
- **Permission Errors**: Fixed Streamlit Cloud filesystem permission issues
- **Excessive Polling**: Reduced API load by 60-75% through exponential backoff
