# Glossary — Predictions / Risk Factor API

**Date:** 2026-08-14  
**Purpose:** Plain-language definitions with code provenance so panels, decks, and eval scripts stop talking past each other.

Code paths below are in the predictions worktree unless noted:  
`~/.cursor/worktrees/predictions-f487c957/verityngn-core-commercial-2c6d35116c0f/`

---

## Flags stamped on video output

### `live_gemini`

Boolean on each video’s multisense JSON.

**True only if all of:**

1. `MULTISENSE_OFFLINE` is not set (and `offline=False`)
2. A GenAI client authenticated (`_get_genai_client()` succeeded)
3. A video URL or GCS URI was supplied
4. Tier A returned `source == "gemini"`

Set at `verityngn/services/fusion/gemini_multisense.py` (`live_gemini`: `bool(use_live and tier_a.get("source") == "gemini")`).

**`False` means:** the delivery track was written by `_offline_tier_a()` — a keyword heuristic over claim text. No model watched the video. Every Karp corpus row as of 2026-08-14 is `False`.

### `signal_tier`

- **`interpreted`** — a model’s opinion of the video (Gemini Tier A/B). Constant `"interpreted"` in `gemini_multisense.py`.
- **`measured`** — a number from the waveform (prosody, VAD) or pixels (AU, gaze, rPPG). Stamped in `fusion/schema.py`.

### `prosody_proxy`

Source tag on dimensional affect. Valence / arousal / dominance were mapped from pitch and energy by `_proxy_from_prosody()` in `affect/adapters/audeering_vad.py`. The real model is `audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim`. Install `torch` + `transformers` and a long-enough WAV window and the tag becomes `audeering_wav2vec2`.

### `offline_proxy`

Gemini’s fallback source string when live video inference did not run. Same idea as `prosody_proxy`, for the interpreted lane.

### `MULTISENSE_ENABLED`

Env gate (`0`/`1`). `run_multisense()` is a no-op unless this is `1` or `force=True`. `verityngn/services/fusion/run_multisense.py`.

### `MULTISENSE_OFFLINE`

Env gate. Forces `_offline_tier_a` / Jaccard derailment even if credentials exist.

---

## Metrics

### VAD (here)

**Valence / Arousal / Dominance** — a 3-axis affect score — **not** Voice Activity Detection.

| Axis | Meaning |
|------|---------|
| Valence | unpleasant ↔ pleasant |
| Arousal | calm ↔ excited |
| Dominance | submissive ↔ dominant |

### CAR

**Cumulative Abnormal Return.** What it *should* be: stock return around an event, minus expected return from a market model (beta vs SPY, estimation window `[-250, -30]`), summed over horizon H trading days.

What T010 computed through 2026-08-14: a **single-session raw close-to-close** on the first trade on/after the print. Neither cumulative nor abnormal. Honest name until market-model code lands: `raw_h1`. Implementation: `scripts/karp_earnings_effect.py` `_car_h1`; market-model path: `verityngn/services/timeseries/returns.py`.

Horizons used in the harness: **H = 1, 5, 10, 21** (plus 30 in the synthetic scaffold).

### IC / ICIR

- **IC (information coefficient)** — Spearman rank correlation of the factor vs the outcome, one observation set at a time.
- **ICIR** — mean IC / std IC. Gate: **≥ 0.40**.

Calendar `daily_rank_ic` in `verityngn/services/quant/ic.py` needs **≥ 3 names on the same date**. Staggered earnings almost never have that, so `n: 0` and ICIR is undefined by construction. Use `event_time_ic()` instead.

### Breadth

Number of independent bets per year. Grinold: **IR = IC × √breadth**.

25 CEOs × 4 prints/yr ≈ 100 video-lane bets. At IC = 0.03 that is IR ≈ 0.30. Text filings (thousands of events) carry the statistical load; video is the differentiator.

### RankIC vs event-time IC

| Design | Groups by | Breaks when |
|--------|-----------|-------------|
| `daily_rank_ic` | calendar date | One ticker prints per day |
| `event_time_ic` | all events (pooled) or event-week buckets | n_events &lt; 3 |

### DSR

Deflated Sharpe Ratio (Bailey & López de Prado). Probability the observed Sharpe is real after counting every trial in `docs/trials_ledger.md`. Gate: **≥ 0.95**. Formula in `verityngn/services/quant/deflated_sharpe.py`.

### Fidelity

Fraction of a factor’s inputs that are **measured** rather than proxy, synthetic, or a defaulted constant. Constants (e.g. missing `sympathetic_arousal` filled with 0.5) count as zero. See `verityngn/services/quant/signal_quality.py`.

### NuisanceLeak

`max |Spearman(factor, nuisance)|` over `{n_claims, duration_sec, n_segments, venue, days_to_print}`. On the 2026-08-14 Karp panel, Spearman(n_claims, S01) ≈ **0.77** — S01 was tracking video length, not delivery. Target **&lt; 0.20**. Residualize via `verityngn/services/quant/nuisance.py`.

### Power

`n_events / n_required(rho_target=0.20)` capped at 1. Detecting ρ = 0.20 at 80% power needs **≈194** events. T010 has 6.

### L (signal-quality loss)

`L = 0.30(1−Fidelity) + 0.30·NuisanceLeak + 0.20(1−Power) + 0.15(1−ICIRnorm) + 0.05·DeflationGap`

Keep an iteration only if L strictly decreases. Stop when L &lt; 0.25 **and** NuisanceLeak &lt; 0.2 **and** Power ≥ 1.

---

## Product / process tokens

### `NO_PROMOTE`

Risk factor **not validated for allocation**. Hygiene gates in `docs/trials_ledger.md` must pass first. Factor PASS ≠ portfolio PROMOTE.

### `INSTRUMENT_ONLY`

A row or factor whose Fidelity is below the floor. May be shown on an instrumentation panel; must not enter a market test.

### Congruence (S01)

Text / voice / face agreement. **High congruence ≠ truth.** Drift down = split delivery. Formula in `fusion/crossmodal.py`: historically 0.40·text-voice + 0.35·voice-face + 0.25·face-text. Missing channels are **omitted and weights renormalized** — never filled with 0.5.

### S14 caveat

Hobson / Mayew vocal-dissonance accuracy is only ~8–17% above chance. Ship that caveat with the number or do not ship the row.

---

## Related docs

- [GATES_GLOSSARY.md](GATES_GLOSSARY.md) — Family A instrument vs Family B allocation gates
- [VIDEO_CUE_CRITICAL_RATING.md](VIDEO_CUE_CRITICAL_RATING.md) — PASS/WEAK/FAIL cue grades + MediaPipe
- [USEFULNESS_RUNGS.md](USEFULNESS_RUNGS.md) — U1 / U2 / U3 without pretending n=7 is 194
- [RISK_LEXICON.md](RISK_LEXICON.md) — signal → risk factor language
- [RISK_FACTOR_REGISTRY_S00_S15.md](RISK_FACTOR_REGISTRY_S00_S15.md)
- [CEO_CORPUS_SOURCING_DEEPRESEARCH.md](CEO_CORPUS_SOURCING_DEEPRESEARCH.md)
