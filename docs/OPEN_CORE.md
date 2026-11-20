# Open-Core Boundary — VerityNgn OSS v3.0.1

**Effective:** 2026-11-13 (collateral refresh; PyPI `3.0.1` immutable for Monday Nov 16 launch)  
**Rule:** `verityngn-oss` is the **canonical engine and research feature tree**. Commercial repos add **hosted scale, billing, and packaging** only. Predictions / MultiSense / vision / audio sleeves are **absorbed in OSS** — not commercial-only.

## OSS (`verityngn-oss`) — public Apache-2.0

User-facing product language: **claim-level risk abatement** (disclosure / delivery / sponsor-readiness). Internal model still uses TRUE/FALSE/UNCERTAIN probabilities (display: Supported / Contested / Unresolved).

### Engine (default-on in `verityngn==3.0.1`)

- Multimodal analysis + claim extraction with **adaptive 1–6 fps** scene sampling
- Pixel claim modalities (`visual_text` / `graphic` / `chart` / `demonstration`) + auto-emitted `brand_safety_scores.json` and `{id}_exhibit_map.json`
- Counter-intelligence (YouTube + press-release + Sherlock CI)
- Verification engine (grounded search, fact-check API, domain tiers, hard timeouts)
- URL safety + report sanitization
- Standard + **Deep Research** risk briefs (JSON, MD, HTML, PDF when Playwright available) with `visual_only_claims`
- CLI: `verityngn analyze` / `local analyze` / `ablate` / `--deep`
- Video pipeline + tutorial clips

### Opt-in sleeves in the same wheel (turning default-on in 3.1 / 3.2)

| Extra / flag | What it adds | Roadmap |
|--------------|--------------|---------|
| `verityngn[vision]` | MediaPipe 478 landmarks, 52 blendshapes, HFAsy_proxy, blink/gaze, `--story-arc` | 3.2 congruence default-on |
| `verityngn[audio]` | Librosa prosody, VAD, TTS/synthetic voice cues | 3.2 congruence default-on |
| `verityngn[predictions]` + `MULTISENSE_ENABLED=1` | S00–S15 registry, Tier A/B clip congruence | 3.2 delivery/conviction track |
| `VN_AGENTIC_VIDEO=1` | Gemini `mediaProcessing=AGENTIC` frame search | 3.1 object/action semantics |
| AuthenticityGate | C2PA / CorSound / rPPG fail-closed provenance | stays fail-closed |

**Research tree in OSS:** `services/predictions/`, `quant/`, `fusion/`, `players/`, `affect/`, `mediasphere/`, `text_risk/`, `timeseries/`, vision AU/gaze extractors, `scripts/predictions/` (opt-in; not on default `analyze` path).

**Distribution:** GitHub, PyPI (`pip install 'verityngn[deep]==3.0.1'` · optional `[vision,audio,predictions]`), Docker, Streamlit demo.

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
