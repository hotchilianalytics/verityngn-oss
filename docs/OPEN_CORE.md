# Open-Core Boundary — VerityNgn OSS v3

**Effective:** 2026-08-29 (v3.0.0)  
**Rule:** `verityngn-oss` is the **canonical engine**. Commercial, predictions, and riskfactor repos **depend on OSS** and add closed overlays.

## OSS (`verityngn-oss`) — public Apache-2.0 engine

- Multimodal analysis + claim extraction
- Counter-intelligence (YouTube + press-release + Sherlock CI)
- Verification engine (grounded search, fact-check API, domain tiers, hard timeouts)
- URL safety + report sanitization
- Standard + **Deep Research** reports (JSON, MD, HTML, PDF when Playwright available)
- Combined TL;DR + DR + standard assembler
- CLI: `verityngn analyze <url>` / `--file` / `--deep`
- Video pipeline + tutorial clips
- Optional authenticity gate adapters + spectral AI-voice cues + MediaPipe Face Landmarker

**Distribution:** GitHub, PyPI (`pip install verityngn`), Docker, Streamlit demo.

**Rule:** Engine quality improvements land in OSS **first**. Overlay repos import or pin OSS ≥3.0.0.

## Commercial overlay (closed)

| Capability | Location |
|------------|----------|
| Hosted multi-tenant API + batch | `verityngn-backend-commercial` |
| Trial credits / compliance audit | backend `/trial`, `/compliance` |
| User-scoped GCS gallery | backend gallery |
| Legal/agency dossier packaging + outreach | commercial docs/scripts |
| VerityEngine SaaS UI | Replit / verityindex.com |

## Predictions overlay (closed — not in OSS)

- Signal engine, CAR/ICIR, Family A/B gates, Karp panels
- `services/predictions/`, `services/quant/`, fusion derailment/earnings joins
- Depends on OSS ≥3.0.0 for shared video/claims/DR engine

## Riskfactor overlay (closed — future repo)

- S00–S15 registry product surface
- Depends on OSS ≥3.0.0; never merge registry into Apache tree

## Deferred to later OSS absorb

- Full Gemini multisense fusion stack (lives in predictions until a future OSS feature release)

## What must never be commercial-only

Verification logic, counter-intel, standard/DR report quality, URL safety, domain tiers — if hoarded commercially, that is a bug in the open-core model.
