# Gates glossary — instrument vs allocation

**Date:** 2026-08-20  
**Worktree:** `verityindex-predictions`  
**Rule:** Never mix Family A and Family B in the same panel heading. A useful player risk panel can clear Family A (or be honest about failing it) without clearing Family B.

Code: `verityngn/services/quant/signal_quality.py`, `docs/trials_ledger.md`.

Language lock: congruence / delivery-risk / disclosure-risk. **Not** a lie detector. Factor PASS ≠ portfolio PROMOTE.

---

## Two families

| Family | Question it answers | When it applies |
|--------|---------------------|-----------------|
| **A — Instrument hygiene (L-loop)** | Is this number from real sensors, not length/venue proxies? | Every iteration on the Karp panel |
| **B — Allocation hygiene** | May this factor enter a book? | Only after Family A stop conditions *and* a real event study |

T016 freeze (honest n=7): L = **0.706 REJECT**, Fidelity **0.429**, NuisanceLeak **0.469**, Power **6/194**, ICIR **null**, face **0/7**, `live_gemini` **1/7**. Still **NO_PROMOTE**.

---

## Family A — instrument hygiene (L-loop)

Source: `verityngn/services/quant/signal_quality.py`.

**Loop rule:** keep an iteration only if **L strictly decreases**.  
**Stop when:** `L < 0.25` **and** `NuisanceLeak < 0.20` **and** `Power ≥ 1`.

\[
L = 0.30(1-F) + 0.30\cdot\text{NuisanceLeak} + 0.20(1-\text{Power}) + 0.15(1-\text{ICIRnorm}) + 0.05\cdot\text{DeflationGap}
\]

### Fidelity ≥ 0.60

**What:** Fraction of `{audio_source, gemini_source, vision_source, asr_source, sympathetic_arousal}` that is *measured*, not `prosody_proxy` / `offline_proxy` / synthetic / hash-seeded.

**Goal:** ≥ **0.60** (three of five sensors real). Below → stamp `instrument_only`.

**Why that number:** Today audio + ASR are already measured on 7/7. Live Gemini is the cheapest third bit (`audio+ASR+live ≈ 0.60` without face). T015 taught us a pretty L from a missing mp4 is a lie — Fidelity is the anti-artifact gate.

**T016:** **0.429** (7/7 VAD+ASR, 1/7 live Gemini, 0/7 face, no rPPG).

### NuisanceLeak < 0.20

**What:** `max |Spearman(factor, {n_claims, duration_sec, n_segments, days_to_print})|` (venue handled via residualizer one-hots).

**Goal:** < **0.20** on the factor that would enter a market test (prefer residualized S01).

**Why:** Early Karp S01 tracked interview length (~0.77), not delivery. Honest T016 leak is **0.469**. Residualize via `verityngn/services/quant/nuisance.py`; do not celebrate high congruence that is “more claims.”

**Do not** add CEOs to “fix” leak. Fix the factor.

### Power → 1.0 at n = 194

**What:** `n_events / N_REQUIRED_RHO20` capped at 1. `N_REQUIRED_RHO20 = 194` = Fisher-z sample size for Spearman ρ = **0.20**, 80% power, two-sided α = 0.05.

**Goal:** Power = 1.0 for a *market association* claim.

**Why:** Detecting ρ = 0.20 at conventional power needs ~194 independent events. At n=7 / T010’s 6 CAR joins, the panel is **underpowered by construction**. Honest caption: video is the differentiator, not the statistical engine.

**Breadth math (Grinold):** 25 CEOs × 4 prints/yr ≈ 100 video-lane bets/year. At IC = 0.03, IR ≈ 0.30. Text filings (S15) carry significance while video stays sparse.

### ICIRnorm

**What:** `min(|ICIR| / 0.40, 1)`. ICIR = mean IC / std IC. Gate floor **0.40**.

**Why 0.40:** hca-qngn allocation bar (aggressive vs typical equity IC 0.03–0.10). Undefined until `event_time_ic()` has n≥3 with a real outcome. Calendar `daily_rank_ic` stays empty on staggered CEO prints — use event-time IC, not date-grouped rank IC.

**T016:** ICIR **null** → ICIRnorm **0**.

### DeflationGap = 1 − DSR

**What:** Bailey & López de Prado Deflated Sharpe Probability. Every row in `docs/trials_ledger.md` counts in the denominator (18 trials at T016).

**Why:** Unlogged search is how fake Sharpes happen. Count failures.

### `live_gemini`

**What:** Boolean per video. True only if live GenAI watched the video (`source == "gemini"`), not `_offline_tier_a` keyword heuristic.

**Role:** Fidelity bit, **not** a promote gate. False means no model watched the video.

### Product tokens

| Token | Meaning |
|-------|---------|
| `NO_PROMOTE` | Risk factor not validated for allocation |
| `INSTRUMENT_ONLY` | Fidelity below floor; show on instrumentation panel only |
| Factor PASS ≠ portfolio PROMOTE | Family A stop ≠ Family B clear |

### T016 vs Family A (honest)

| Component | T016 | Target |
|-----------|------|--------|
| L | **0.706** REJECT | < 0.25 |
| Fidelity | 0.429 | ≥ 0.60 |
| NuisanceLeak | 0.469 | < 0.20 |
| Power | 6/194 | 1.0 |
| ICIRnorm | 0 | 1.0 |
| Face / rPPG | 0/7 | measured |
| `live_gemini` | 1/7 | 7/7 |

Largest L terms: **1−Power**, then **1−Fidelity**, then leak. Do not revert V7m (T015 leak was a missing-mp4 artifact).

---

## Family B — allocation hygiene (do not apply to n=7)

Source: `docs/trials_ledger.md` (mirrored from hca-qngn).

| Gate | Threshold | Why it exists |
|------|-----------|---------------|
| ICIR | ≥ 0.40 | Stop weak rank correlations from becoming a book |
| Frac IC+ | ≥ 0.55 | Require more positive than negative IC periods |
| Weekly Jaccard | < 0.25 | Kill copycat / overlapping bets |
| Neutralization | resid ICIR ≥ 0.5 × raw | Factor must survive known covariates |
| Cost edge | Q5−Q1 > drag @ 10 bps (hygiene) / 20 bps (promote) | Gross edge must beat turnover |
| DSR | ≥ 0.95 | Prob(Sharpe is real) after trial count |

These exist to stop a backtest from becoming a book. They are **not** the definition of a useful CEO risk panel (see U1 in `USEFULNESS_RUNGS.md`).

---

## Related docs

- [GLOSSARY_SIGNAL_TERMS.md](GLOSSARY_SIGNAL_TERMS.md) — Fidelity, CAR/`raw_h1`, VAD axes
- [SIGNAL_QUALITY_BASELINE.md](SIGNAL_QUALITY_BASELINE.md) — T012–T016 numbers
- [VIDEO_CUE_CRITICAL_RATING.md](VIDEO_CUE_CRITICAL_RATING.md) — what cues are worth computing
- [USEFULNESS_RUNGS.md](USEFULNESS_RUNGS.md) — U1 / U2 / U3 without pretending n=7 is 194
