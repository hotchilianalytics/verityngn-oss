# PARITY_TEST v3.0.0 — OSS vs commercial engine smoke

**Date:** 2026-08-29  
**Goal:** Confirm OSS v3 standard + Deep Research parity with commercial core engine quality (not SaaS delivery).

## Scope

| In | Out |
|----|-----|
| Claim extraction, CI, verification, reports | Predictions / Karp / quant |
| Deep Research grounded pass | Trial credits / multi-tenant gallery |
| Authenticity stubs + spectral cues | Fusion derailment / earnings |

## Procedure

1. Same public demo video ID (gallery approved sample, e.g. prior Lipozem / climate demo).
2. OSS checkout `release/v3.0.0`:
   ```bash
   pip install -e ".[deep]"
   verityngn analyze <url> -o /tmp/oss_v3 --deep
   ```
3. Commercial core (same credentials): run standard + DR on same URL.
4. Compare axes from `PARITY_TEST_20260703.md`:
   - Claim count ±20%
   - Self-referential evidence stripped in DR sanitized input
   - Grounding JSON present
   - Combined report HTML generated when DR succeeds

## Record

| Axis | OSS | Commercial | Pass? |
|------|-----|------------|-------|
| Standard report MD/HTML/JSON | | | |
| Claims count | | | |
| DR markdown + grounding | | | |
| Combined report | | | |
| Boundary scrub (`scripts/ci/open_core_boundary_scan.py`) | OK | n/a | |

**Operator sign-off:** _________________ date ________

Automated unit coverage for DR sanitize/gate/mock LLM and authenticity stubs is in CI; this document is the live Vertex/Gemini smoke checklist.
