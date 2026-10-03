# RELEASE_TEST_MATRIX v3.0.0

**Candidate SHA:** `e12a55b` (includes analyst freeze `5258292` + local-file Vertex genai fix)  
**Branch:** `release/v3.0.0`  
**Date:** 2026-10-03  
**Package version:** 3.0.0

## Offline

| Gate | Command | Result | Notes |
|------|---------|--------|-------|
| Claim-kind unit tests | `pytest test/unit/test_claim_kind.py -q` | **PASS** | 12 passed |
| Open-core boundary | `python scripts/ci/open_core_boundary_scan.py` | **PASS** | clean |
| SB1507 taxonomy scorecard (Sep 23 smoke JSON) | `python scripts/sb1507_risk_taxonomy_scorecard.py` | **PASS** | 28 claims; §6.1=13; quant→inference 83.3%; `all_green=true` |

## Live

| Gate | Fixture | Pass criteria | Result | Notes |
|------|---------|---------------|--------|-------|
| Lipozem old ladder | `tLJC8hkK-ao` full+deep → `outputs/release_v3_lipozem` | claims>0; genre `consumer_factual`; §9 CRAAP; `deep.html`; clinical % stays `source_backed_fact` | **PASS** | 40 claims; all `source_backed_fact`; CRAAP §9; `deep.html` present; clinical-% claim source-backed |
| Lipozem light (supplemental) | `--tier light` → `outputs/release_v3_lipozem_light` | DR-direct completes | **PASS** | `*_direct_risk_report.html` |
| SB1507 analyst lanes | local `sb1507.mp4` local-full → `outputs/release_v3_sb1507` | claims>0; genre `analyst`; §9 SIFT; risk chips; §6.1 ≤ half; scorecard green on **new** JSON | **PARTIAL** | **PASS:** genre=`analyst`, SIFT §9, 5/5 chips, deep completed. **FAIL density:** live extract only **5** claims (3 facts → §6.1 > half); scorecard `all_green=false`. Offline 28-claim smoke remains taxonomy-green. Claim under-recall on this local-full pass — not a CRAAP/SIFT wiring bug. |
| Vertex / 0-claims stop | either run | Fix `VERTEX_LOCATION=global` if 0 claims | **PASS** | Local path fixed: ChatVertexAI → google.genai fallback (`analysis.py`). Runs use `VERTEX_LOCATION=global`. |

## Scorecard thresholds (analyst fixture)

| Threshold | Offline smoke | Live release_v3_sb1507 |
|-----------|---------------|------------------------|
| quant→inference ≥60% | 83.3% PASS | 100% PASS (n=1 quant) |
| §6.1 ≤ half total | 13/28 PASS | 3/5 FAIL |
| no future→LIKELY_FALSE | PASS | PASS |
| deeper not flooded | PASS | PASS |

## Sign-off

| Role | Status |
|------|--------|
| Offline gates | **PASS** |
| Lipozem live (old features) | **PASS** |
| SB1507 live (new features wiring) | **PARTIAL** — SIFT/chips/genre green; density gate needs richer extract or accept offline smoke as density proof |
| Marketing / retag | **Blocked** until operator accepts PARTIAL SB1507 density **or** a re-run hits §6.1 ≤ half; then explicit ask for retag/merge/PyPI |

## Operator decision

Recommended for this cut:

1. Treat **taxonomy + genre wiring** as proven (offline scorecard + live SIFT/chips + Lipozem CRAAP).
2. File a follow-up to raise local-full claim recall on analyst uploads (5 vs historical 28).
3. Retag only after you accept that tradeoff or re-run SB1507 with more claims.
