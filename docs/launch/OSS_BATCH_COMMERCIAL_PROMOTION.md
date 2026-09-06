# OSS to Batch to Commercial Promotion

This checklist is the operating sequence for promoting engine changes from
`verityngn-oss` into Cloud Run Batch and the older commercial overlays.

## Scope

- OSS engine branch: `release/v3.0.0`
- Batch runtime: `~/proj/verityngn-cloudrun-batch`
- Commercial overlays:
  - `~/proj/commercial/verityngn-core-commercial`
  - `~/proj/commercial/verityngn-backend-commercial`

## Rules

1. Do not merge `release/v3.0.0` into `main` as part of this checklist.
2. Treat OSS as the canonical engine.
3. Promote Batch only after OSS smoke passes.
4. Reintegrate commercial by dependency pin / backport discipline, not a broad
   reverse merge.
5. Keep `VN_AGENTIC_VIDEO` opt-in until a separate production ablation says
   otherwise.

## Commit Sequence

1. `fallback-runtime`
   - shared Vertex/model/API fallback
   - runtime defaults and logs
2. `docs-and-papers-refresh`
   - README, methodology, architecture, setup, testing, papers
3. `test-and-collateral-refresh`
   - trials ledger, release checklist, any new regression tests

## OSS Validation Gate

Before push:

1. Unit tests:
   - `pytest -q test/unit/test_llm_fallback.py`
   - `pytest -q test/unit/test_deepresearch.py`
   - `pytest -q test/unit/test_sufficiency.py`
2. Focused smoke:
   - `tLJC8hkK-ao`
   - `sb1507.mp4`
3. Failure-path smoke:
   - force an unavailable model/region and confirm fallback lands on a working
     backend
4. Confirm output contract:
   - `report.html`
   - `deep.html`
   - `{video_id}_report.json`
5. Update `docs/trials_ledger.md`

## Push / Tag Candidate

1. Review `git diff` on `release/v3.0.0`
2. Commit in the sequence above
3. Push branch
4. Choose the promoted engine ref:
   - preferred: release tag such as `v3.0.0` or `v3.0.x`
   - acceptable during pre-cutover smoke: `release/v3.0.0`

## Cloud Run Batch Promotion

1. Update batch repo to consume the promoted OSS ref, not `main`
2. Align runtime env:
   - `VERTEX_MODEL_NAME=gemini-3.8-flash`
   - `AGENT_MODEL_NAME=gemini-3.8-flash`
   - `VERIFICATION_MODEL_NAME=gemini-3.8-flash`
   - `VERTEX_LOCATION=global`
   - `VERTEX_FALLBACK_LOCATIONS=global,us-central1`
   - `VERTEX_FALLBACK_MODELS=gemini-3.6-flash,gemini-2.5-flash`
3. Deploy in order:
   - batch image
   - one batch smoke job
   - Cloud Run API
4. Verify logs show selected backend/model/location and fallback hops when used

## Commercial Re-integration

1. Replace stale engine refs with the promoted OSS pin
2. Run parity checks against `PARITY_TEST_v3.md`
3. Reapply overlay-only logic:
   - auth / tenancy
   - billing / credits
   - storage scoping
   - frontend contract glue
4. Document divergences from OSS explicitly

## Rollback

If Batch or commercial parity fails:

1. revert overlay/runtime pin to the last known-good OSS ref
2. keep OSS branch intact
3. log the failure mode in `docs/trials_ledger.md`
