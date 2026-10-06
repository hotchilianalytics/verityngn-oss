# Sherlock — gates, video cues, useful n (2026-08-20)

**Worktree:** `~/.cursor/worktrees/predictions-f487c957/verityngn-core-commercial-2c6d35116c0f`  
**Branch:** `verityindex-predictions`  
**Canvas:** `canvases/sherlock-gates-cues.canvas.tsx` (workspace canvases dir)

## Problem

Useful CEO risk panel felt unreachable because (1) Family A instrument gates were conflated with Family B allocation gates, (2) face was omitted on 7/7 so S01 could not be Oxford-Man modal incongruence, (3) Power/194 was treated as the definition of “done.”

## Steps 1–2 (distilled)

- Split gates (glossary).  
- Turn on measured face via MediaPipe Face Landmarker.  
- Grow usefulness via U1 panel → U2 S15 text → U3 more CNBC videos — without waiting on ICIR/DSR.

## What shipped

| Deliverable | Path |
|-------------|------|
| Gates glossary | `docs/predictions/GATES_GLOSSARY.md` |
| Cue critical rating | `docs/predictions/VIDEO_CUE_CRITICAL_RATING.md` |
| Usefulness rungs U1–U3 | `docs/predictions/USEFULNESS_RUNGS.md` |
| Canvas | workspace `canvases/sherlock-gates-cues.canvas.tsx` |
| MediaPipe adapter (IMAGE mode, HFAsy_proxy) | `verityngn/services/vision/adapters/mediapipe.py` |
| T018 runner | `scripts/run_mediapipe_karp.py` |
| Residualize runner | `scripts/residualize_s01_karp.py` |
| Fidelity allowlist + unknown-tag fix | `verityngn/services/quant/signal_quality.py` |
| Live Gemini report discovery | `scripts/run_live_gemini_one.py` → `_final_report.json` |

## Trials

| Trial | Result |
|-------|--------|
| **T017** | live_gemini **5/7** (QNk, dRg, V7m, ijR, WBu9). xe84 + pHu: Vertex **429** after cooldown. |
| **T018** | MediaPipe face on **4/7** (QNk, WBu9, pHu, ijR). cov 0.68–0.86. HFAsy_proxy 0.066–0.119. Pin `mediapipe==0.10.18` (1.0 Metal crash). |

## Scores vs T016

| Metric | T016 | T017+T018 |
|--------|------|-----------|
| L | 0.706 REJECT | **0.603 KEEP** |
| Fidelity | 0.429 | **0.771** |
| Leak raw | 0.469 | 0.469 |
| Leak resid | — | **0.306** (still > 0.20) |
| instrument_only | true | **false** (Fidelity floor cleared) |
| promote | NO_PROMOTE | **NO_PROMOTE** |

## Next

1. Retry xe84 + pHu live Gemini after quota cools.  
2. Residualize harder / more covariates until resid leak < 0.20.  
3. Do **not** add CEOs until resid leak < 0.20 (Fidelity already ≥ 0.60).  
4. U2: S15 text sleeve for significance.  
5. U3: expand CNBC talking-head catalog (Karp then Huang).

## Language lock

Congruence / delivery-risk / disclosure-risk. Not a lie detector. HFAsy_proxy ≠ Banker CNN HFAsy.
