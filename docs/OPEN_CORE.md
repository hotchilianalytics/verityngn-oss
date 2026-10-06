# Open-Core Boundary — VerityNgn OSS v3

**Effective:** 2026-10-05 (predictions absorb)  
**Rule:** `verityngn-oss` is the **canonical engine and research feature tree**. Commercial repos add **hosted scale, billing, and packaging** only.

## OSS (`verityngn-oss`) — public Apache-2.0

User-facing product language: **claim-level risk abatement** (disclosure / delivery / sponsor-readiness). Internal model still uses TRUE/FALSE/UNCERTAIN probabilities (display: Supported / Contested / Unresolved).

### Engine

- Multimodal analysis + claim extraction
- Counter-intelligence (YouTube + press-release + Sherlock CI)
- Verification engine (grounded search, fact-check API, domain tiers, hard timeouts)
- URL safety + report sanitization
- Standard + **Deep Research** risk briefs (JSON, MD, HTML, PDF when Playwright available)
- CLI: `verityngn analyze` / `local analyze` / `ablate` / `--deep`
- Video pipeline + tutorial clips
- Optional authenticity adapters, spectral AI-voice cues, MediaPipe Face Landmarker, story-arc continuity stub
- Optional agentic video spike (`VN_AGENTIC_VIDEO`)

### Research features (in OSS)

- Predictions / RiskFactor sensors (S00–S15 registry docs + scripts)
- `services/predictions/`, `quant/`, `fusion/`, `players/`, `affect/`, `mediasphere/`, `text_risk/`, `timeseries/`
- Vision AU/gaze/landmarks extractors and optional adapters
- Opt-in scripts under `scripts/predictions/` (not on the default `analyze` path)

**Distribution:** GitHub, PyPI (`pip install verityngn[predictions]`), Docker, Streamlit demo.

**Rule:** Engine and research quality improvements land in OSS **first**.

## Commercial overlay (hosted only)

| Capability | Location |
|------------|----------|
| Hosted multi-tenant API + batch | `verityngn-backend-commercial` |
| Trial credits / compliance audit / Stripe | backend `/trial`, `/compliance`, billing |
| User-scoped GCS gallery | backend gallery (`verityindex_commercial` paths) |
| Legal/agency dossier packaging + outreach | commercial docs/scripts |
| VerityEngine SaaS UI | Replit / verityindex.com |
| Cloud Run scale / production SLOs | commercial + batch images pinning OSS |

## What must never be commercial-only

Verification logic, counter-intel, standard/DR report quality, URL safety, domain tiers, and research RiskFactor sensors — if hoarded commercially, that is a bug in the open-core model.
