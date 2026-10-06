# Factor scorecard — L and NuisanceLeak (Karp n=7)

**Date:** 2026-08-26  
**Worktree:** `verityindex-predictions` (`verityngn-core-commercial` predictions worktree)  
**Panel:** PLTR / Alex Karp CEO delivery-risk (n=7)  
**Promote:** leak gate **cleared** (T019 resid N **0.1261** &lt; 0.20); multimodal still **`NO_PROMOTE`** for allocation (Power/ICIR). Fidelity ≥ 0.60.

Baseline frozen from T017+T018 / `data/predictions/quant/signal_quality.json` + `signal_quality_resid.json` before T019 covariates.

---

## A. Composite loss L

\[
L = 0.30(1-F) + 0.30\cdot N + 0.20(1-P) + 0.15(1-I) + 0.05\cdot D
\]

| Symbol | Name | Weight | Definition | Baseline | Gate / role |
|--------|------|--------|------------|----------|-------------|
| **F** | Fidelity | 0.30 | Mean of 5 measured bits: audio, gemini, vision, asr, sympathetic arousal (proxy/synthetic = 0) | **0.7714** | ≥ 0.60 cleared |
| **N** | NuisanceLeak | 0.30 | `max \|Spearman(factor, nuisance)\|` over `{n_claims, duration_sec, n_segments, days_to_print}` | raw **0.4685** / resid **0.3063** | resid **&lt; 0.20** (this sprint) |
| **P** | Power | 0.20 | `min(n_events/194, 1)` | **0.0309** (6/194) | Not leak fix |
| **I** | ICIRnorm | 0.15 | `min(\|ICIR\|/0.40, 1)` | **0** (null ICIR) | Defer |
| **D** | DeflationGap | 0.05 | `1 − DSR` | **0.9978** | Log trials; do not game |

| Score view | L | KEEP rule |
|------------|---|-----------|
| Raw factor `s01_congruence` | **0.6028** | KEEP vs T016 0.7057 |
| Resid factor `s01_congruence_resid` | **0.5542** | Prefer L↓ each trial |

**Loop:** register trial → change **one** thing → re-score → KEEP only if **L strictly decreases**. Reject ICIR-up / leak-up.

Code: `verityngn/services/quant/signal_quality.py`, `scripts/score_signal_quality.py`.

---

## B. NuisanceLeak sub-factors (attack order)

| Sub-factor | Role | Baseline resid \|ρ\| | Action |
|------------|------|----------------------|--------|
| **n_claims** | Claim-count length proxy | **0.3063** | Primary |
| **n_segments** | Segment-count (collinear with claims on this panel) | **0.3063** | Confirm; often = n_claims |
| **duration_sec** | Wall-clock length | **null** | **T019:** populate via ffprobe |
| **days_to_print** | Days from recording to next earnings print | **null** | **T019:** from `karp_earnings_effect.json` where known |
| venue | Format prior (one-hot in residualizer) | unused/empty | **T019:** stamp interview/keynote/cnbc/davos |

Residualizer: `verityngn/services/quant/nuisance.py` (`residualize_rows`).

---

## C. Delivery-risk factors (S00–S15) — leak touch list

| ID | Name | Touch for leak? | Note |
|----|------|-----------------|------|
| **S01** | Cross-channel congruence | **Primary** | Leak is measured on S01 / S01_resid |
| S00 | Media provenance | Gate only | Authenticity |
| S02 | Interpreted vs measured | Secondary | Gemini/prosody gap |
| S03–S08 | Audio sleeves | Secondary | Only if fusion overweight long audio |
| S09/S12/S13 | Vision / face / incongruence | Secondary | T021 face completion |
| S10 | Claim-report coupling | Check | Must not dominate fusion |
| S11/S14 | Text / vocal research | Avoid selling S14 | Research-only |
| S15 | Disclosure-Risk Text | Out of scope | GC text product lane |

Registry: `docs/predictions/RISK_FACTOR_REGISTRY_S00_S15.md`.

---

## D. Per-video baseline (pre-T019)

| video_id | n_claims | s01_congruence | s01_congruence_resid | live_gemini | vision_source | sympathetic_arousal |
|----------|----------|----------------|----------------------|-------------|---------------|---------------------|
| QNkPpVYagRc | 5 | 0.483 | −0.167 | true | mediapipe_face_landmarker | 0.0285 |
| dRgPbNJ5RJc | 6 | 0.866 | +0.214 | true | — | — |
| V7mYWOzdhpc | 38 | 0.848 | +0.123 | true | — | — |
| ijRuuaaM6XM | 26 | 0.589 | −0.109 | true | mediapipe_face_landmarker | 0.0278 |
| xe84cwQJKaE | 38 | 0.875 | +0.150 | **false** | — | — |
| WBu9Ai6OX3I | 40 | 0.633 | −0.096 | true | mediapipe_face_landmarker | 0.0757 |
| pHu-FarYZlU | 36 | 0.604 | −0.116 | **false** | mediapipe_face_landmarker | 0.0343 |

**Pattern:** short videos (5–6 claims) sit at extremes of resid; high-claim cluster (36–40) still leaves resid leak **0.306** after OLS on claims/segments alone. Missing `duration_sec` under-specifies the residualizer.

**Hard rules:** no new CEOs; no revert V7m; language lock (congruence / delivery-risk / disclosure-risk); multimodal stays `NO_PROMOTE` until resid N &lt; 0.20.

---

## E. Trial plan (this remediation)

| Trial | Change | Success |
|-------|--------|---------|
| **T019** | Populate `duration_sec` + `days_to_print` + `venue`; re-residualize only | resid N ↓ and L ↓ |
| **T020** | If needed: claim-normalized S01 then residualize | resid N &lt; 0.20 or L↓ with N↓ |
| **T021** | If needed: live Gemini on xe84/pHu; face on missing rows | resid N &lt; 0.20 |

Updates after each trial are appended below.

---

## F. Post-trial results (filled during remediation)

### T019 — duration + days_to_print + venue residualize — **KEEP**

Artifact: `data/predictions/quant/signal_quality_resid.json`  
Change: populate `duration_sec` (ffprobe), `days_to_print` (earnings join; QNk imputed median + flag), `venue` ∈ {interview, conference}; residualize with `(n_claims, duration_sec, days_to_print)` + venue one-hots; drop collinear `n_segments` from OLS design. **No S01 formula change.**

| Metric | Pre-T019 | T019 | Δ |
|--------|----------|------|---|
| resid NuisanceLeak | 0.3063 | **0.1261** | ↓ (gate &lt; 0.20 **cleared**) |
| resid L | 0.5542 | **0.5001** | ↓ KEEP |
| raw NuisanceLeak | 0.4685 | **0.8214** (duration now measured) | ↑ honest; promote-candidate is resid |
| Fidelity | 0.7714 | 0.7714 | — |

Driver post-resid: `n_claims` = `n_segments` = 0.1261; `duration_sec` 0.0714.

**LOO caveat (n=7):** leave-one-out resid max\|ρ\| ranges **0.058–0.464** (worst drop = V7m). Full-panel gate is &lt; 0.20; treat 0.126 as panel-conditional, not precise to 0.01.

**Env:** residualizer requires numpy (`sr` env); silent single-covariate fallback removed.

### T020 — claim-normalized S01 — **REJECT_keep_T019**

Artifact: `data/predictions/quant/signal_quality_t020_claim_norm.json`  
Change: `s01_claim_norm = s01 / log1p(n_claims)` then same residualizer.

| Metric | T019 resid | T020 resid |
|--------|------------|------------|
| resid N | 0.1261 | 0.1261 |
| resid L | 0.5001 | 0.5001 |

No L↓ / no further N↓ → reject; keep T019 residual as promote-candidate factor.

### T021 — sensors on leaky rows — **DEFERRED (not required for gate)**

xe84 + pHu still lack live Gemini (historical Vertex 429); dRg + V7m + xe84 still lack face. Full-panel resid N already &lt; 0.20, so sensor completion is Fidelity/robustness work, not the leak unblock. No new CEOs; no V7m revert.

### Gate / SpaceX multimodal

| Check | Value | Unblock SpaceX multimodal? |
|-------|-------|------------------------------|
| resid NuisanceLeak &lt; 0.20 | **0.1261 (T019)** | **yes** (leak gate cleared; LOO fragile) |
| Fidelity ≥ 0.60 | 0.7714 | yes |

**Caveat:** multimodal Delivery-Risk remains provenance / instrument — do **not** sell as allocation alpha (Power≪1, ICIR null). Text-only SpaceX Disclosure-Risk Audit was never blocked by this gate.
