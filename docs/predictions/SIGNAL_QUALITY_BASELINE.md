# Signal-quality baseline (T012–T018)

**Date:** 2026-08-20 (T017+T018)  
**Worktree artifact:** `data/predictions/quant/signal_quality.json`  
**Resid artifact:** `data/predictions/quant/signal_quality_resid.json`  
**Loss:** `L = 0.30(1−F) + 0.30·NuisanceLeak + 0.20(1−Power) + 0.15(1−ICIRnorm) + 0.05·DeflationGap`

| Component | T012 | T014 | T015* | T016 | **T017+T018** | Target |
|-----------|------|------|-------|------|---------------|--------|
| **L** | 0.926 | 0.883 | 0.647* | 0.706 | **0.603 KEEP** | < 0.25 |
| Fidelity | 0.00 | 0.143 | 0.371 | 0.429 | **0.771** | ≥ 0.60 |
| NuisanceLeak raw | 0.775 | 0.775 | 0.216* | 0.469 | **0.469** | < 0.20 |
| NuisanceLeak resid | — | — | — | — | **0.306** | < 0.20 |
| Power | 6/194 | same | same | same | same | 1.0 |
| `live_gemini` | 0/7 | 1/7 | 1/7 | 1/7 | **5/7** | 7/7 |
| Face | 0/7 | 0/7 | 0/7 | 0/7 | **4/7 MediaPipe** | all rows |

\*T015 leak/L used a stub-discarded V7m.  
T017: xe84 + pHu still `offline_proxy` (Vertex 429). Retry later.  
T018: `HFAsy_proxy` on QNk / WBu9 / pHu / ijR — not Banker CNN HFAsy.

**NO_PROMOTE.** Fidelity cleared the 0.60 floor (`instrument_only=false`) but resid leak 0.306 still blocks any market join. Do not add CEOs until resid leak < 0.20.

Gates glossary: [GATES_GLOSSARY.md](GATES_GLOSSARY.md). Cue rating: [VIDEO_CUE_CRITICAL_RATING.md](VIDEO_CUE_CRITICAL_RATING.md).
