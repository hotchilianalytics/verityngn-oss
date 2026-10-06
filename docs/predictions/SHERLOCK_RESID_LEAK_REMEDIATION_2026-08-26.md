# Sherlock — Resid NuisanceLeak remediation (Family A)

**Date:** 2026-08-26  
**Worktree:** `verityindex-predictions` / predictions Karp n=7  
**Goal:** resid NuisanceLeak &lt; 0.20 without new CEOs / without reverting V7m

## Hypotheses → outcome

| # | Hypothesis | Result |
|---|------------|--------|
| 1 | Missing `duration_sec` / `days_to_print` under-specifies OLS | **Confirmed** — T019 resid N 0.306→**0.126** |
| 2 | Collinear `n_claims`/`n_segments` | Confirmed equal ranks; dropped segments from design |
| 3 | Claim-normalized S01 needed | **Rejected** — T020 identical leak/L to T019 |
| 4 | Gemini/face on leaky rows required for gate | **Not required** — T021 deferred; gate cleared on covariates alone |
| 5 | n=7 Spearman unstable | **Confirmed** — LOO resid N 0.058–0.464 |

## Trials

- **T019 KEEP** — covariates + residualize; resid L 0.500; artifact `signal_quality_resid.json`
- **T020 REJECT_keep_T019** — claim-norm; artifact `signal_quality_t020_claim_norm.json`
- **T021 deferred** — xe84/pHu Gemini + missing face; Fidelity work later

## Hardening

`nuisance._ols_resid` now **requires numpy** (no silent single-covariate fallback). Use `sr` (or any numpy) Python for scoring.

## Gate

Full-panel resid N **0.1261 &lt; 0.20** and Fidelity **0.7714 ≥ 0.60** → SpaceX multimodal ablation plan leak-blocker **cleared**, with LOO fragility caveat. Multimodal still **NO_PROMOTE** for allocation (Power/ICIR). Text-only Disclosure-Risk was never blocked.

## Cleanup

No temporary residualizer debug prints added this session. Ask before removing any future debug logs.
