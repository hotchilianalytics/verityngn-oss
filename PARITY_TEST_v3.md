# PARITY_TEST v3.0.0 — OSS vs commercial engine smoke

**Date:** 2026-08-29 (updated 2026-09-01 for tiers + captions)  
**Goal:** Confirm OSS v3 standard + Deep Research parity with commercial core engine quality (not SaaS delivery).

## Scope

| In | Out |
|----|-----|
| Claim extraction, CI, verification, reports | Predictions / Karp / quant |
| Deep Research grounded pass | Trial credits / multi-tenant gallery |
| Analysis tiers + caption_fetch | RiskFactor registry |
| Authenticity stubs + spectral cues | Fusion derailment / earnings |

## Procedure

1. Same public demo video ID (gallery approved sample, e.g. prior Lipozem / climate demo).
2. OSS checkout `release/v3.0.0`:
   ```bash
   pip install -e ".[deep]"
   verityngn captions '<url>'                    # VTT smoke
   verityngn analyze --tier light <url> -o /tmp/oss_light
   verityngn analyze --tier full <url> -o /tmp/oss_full --deep
   ```
3. Commercial core (same credentials): run standard + DR on same URL.
4. Compare axes from `PARITY_TEST_20260703.md`:
   - Claim count ±20% (full tier)
   - DR-direct markdown present (light tier)
   - Self-referential evidence stripped in DR sanitized input
   - Grounding JSON present
   - Combined report HTML generated when DR succeeds
   - `.en.vtt` cached under `outputs/{id}/analysis/`

## Record

| Axis | OSS | Commercial | Pass? |
|------|-----|------------|-------|
| `verityngn captions` → `.en.vtt` | | | |
| Tier `light` DR-direct | | | |
| Tier `full` standard report MD/HTML/JSON | | | |
| Claims count (full) | | | |
| DR markdown + grounding | | | |
| Combined report | | | |
| Boundary scrub (`scripts/ci/open_core_boundary_scan.py`) | OK | n/a | |

**Operator sign-off:** _________________ date ________

Automated unit coverage for caption_fetch, tiers, DR sanitize/gate/mock LLM and authenticity stubs is in CI; this document is the live Vertex/Gemini smoke checklist.
