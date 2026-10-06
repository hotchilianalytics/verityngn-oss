# Predictions Trials Ledger

**Format:** mirrored from hca-qngn `docs/trials_ledger.md`  
**Rule:** Register a row **before** computing hold-out / test metrics. Count every config including failures.

| Date | Label | Bundle | Strategy file | Trials (cumulative) | CAGR | Sharpe | MaxDD | DSR | Notes |
|------|-------|--------|---------------|---------------------|------|--------|-------|-----|-------|
| 2026-08-06 | T000 | predictions-scaffold | timeseries/event_study.py | 1 | — | — | — | — | Scaffold harness; synthetic features; NO_PROMOTE |
| 2026-08-06 | T001 | gallery-affect-sanity | affect/extract.py | 2 | — | — | — | — | Internal QA: affect vs claim confidence; not market |
| 2026-08-06 | T002 | media-exuberance | quant + event_study CAR | 3 | — | — | — | — | **Registered pre-peek.** Target: surprise / CAR H=1..30. NO_PROMOTE until live audio |
| 2026-08-06 | T003 | mediasphere-velocity | mediasphere + quant | 4 | — | — | — | — | **Registered pre-peek.** Musk stress-test for per-speaker norms |
| 2026-08-06 | T004 | congruence-fusion | fusion/crossmodal.py | 5 | — | — | — | — | **Registered pre-peek.** Text–voice–face divergence composite |
| 2026-08-06 | T005 | sympathetic-arousal | vision/spectral.py | 6 | — | — | — | — | **Registered pre-peek.** rPPG + SympCam-style channel; authenticity-gated |
| 2026-08-06 | T006 | fused-composite | fusion/schema.py + hygiene | 7 | — | — | — | — | **Registered pre-peek.** Late-fusion composite; fixture hygiene correctly FAIL (sparse CS) |
| 2026-08-10 | T007 | interpreted-measured-agreement | fusion/gemini_multisense + crossmodal | 8 | — | — | — | — | **Registered pre-peek.** Gemini interpreted vs measured (prosody/VAD) congruence; offline harness in `scripts/calibrate_multisense_agreement.py`. NO_PROMOTE until live Gemini + executive-domain audio |
| 2026-08-10 | T008 | karp-signal-registry-n1 | scripts/build_karp_signal_report.py | 9 | — | — | — | — | **n=1** live Gemini on `QNkPpVYagRc` (CNBC Davos 2024). Seeds S01–S10 for `ceo_pltr_karp`. NO_PROMOTE until ≥5 Karp videos + measured VAD/AU (not prosody_proxy). |
| 2026-08-10 | T008b | karp-corpus-n2 | scripts/build_karp_signal_report.py --corpus-dirs | 10 | — | — | — | — | Added `dRgPbNJ5RJc` (WEF 2026, 35 min, 6 claims, congruence 0.89). Corpus mean S01=0.80. Still NO_PROMOTE (n=2, valence_gap, prosody_proxy). |
| 2026-08-10 | T009 | karp-s11-derailment | fusion/derailment.py | 11 | — | — | — | — | **Registered pre-peek.** Krykoniuk et al. 2026 expected-vs-actual Q&A as S11. Cue only (not disinfo). NO_PROMOTE. |
| 2026-08-10 | T010 | karp-pre-earnings-car | scripts/karp_earnings_effect.py | 12 | — | — | — | — | **Registered before CAR peek.** Five additional pre-print Karp interviews → next PLTR print CAR H=1 vs S01/S05/S11. Leakage-safe (recorded < print). NO_PROMOTE until n≥10 + ICIR gates. |
| 2026-08-26 | T020 | s01-claim-norm-resid | residualize_s01_karp + claim_norm | 22 | — | — | — | — | **REJECT_keep_T019.** `s01/log1p(n_claims)` then residualize → resid N 0.1261 / L 0.500 same as T019. No improvement. NO_PROMOTE. |
| 2026-08-26 | T019 | duration-days-venue-resid | nuisance.py + residualize_s01_karp | 21 | — | — | — | — | **KEEP.** Stamp duration_sec/days_to_print/venue; OLS resid on claims+duration+days+venue (drop segments). resid N 0.306→**0.126** (&lt;0.20); resid L 0.554→**0.500**. Raw leak ↑0.82 on duration (honest). LOO resid N 0.06–0.46. T021 sensors deferred. Leak gate clears SpaceX multimodal *plan* resume; still NO_PROMOTE allocation. |
| 2026-08-20 | T018 | mediapipe-face-landmarker-karp | vision/adapters/mediapipe.py + scripts/run_mediapipe_karp.py | 20 | — | — | — | — | **Scored.** Face on QNk/WBu9/pHu/ijR (cov 0.68–0.86). HFAsy_proxy 0.066–0.119 (not Banker 1:1). S01 face terms restored (renormalize). ijR not coverage-fail at sample_fps=1. mediapipe==0.10.18 IMAGE mode (1.0 Metal crash). NO_PROMOTE. |
| 2026-08-20 | T017 | live-gemini-remaining-six | scripts/run_live_gemini_one.py | 19 | — | — | — | — | **Partial.** live_gemini **5/7** (QNk+dRg+V7m+ijR+WBu9). xe84+pHu hit Vertex 429 RESOURCE_EXHAUSTED after cooldown. Fixed report discovery → `_final_report.json`. L 0.706→~0.61 KEEP vs T016. Fidelity ~0.74. NO_PROMOTE. Retry xe84/pHu later. |
| 2026-08-15 | T016 | karp-v7m-real-mp4-refusion | scripts/run_measured_affect_karp.py + refusion_s01_karp.py | 18 | — | — | — | — | **Scored.** L 0.647→0.706 REJECT (do not revert V7m; T015 leak was missing-mp4 artifact). Honest n=7: Fidelity 0.429, NuisanceLeak 0.469, 7/7 VAD+ASR, live_gemini 1/7, face 0/7. Attribution: docs/predictions/KARP_DELIVERY_ATTRIBUTION.md. NO_PROMOTE. |
| 2026-08-15 | T015 | karp-media-five-refusion | scripts/run_measured_affect_karp.py + fusion/schema.py | 17 | — | — | — | — | **Registered before re-score of L.** Download remaining 5 Karp mp4s; measured VAD+ASR; re-fuse S01 with vision omitted (no 0.5 face fill). No new CEOs. NO_PROMOTE. |
| 2026-08-15 | T014 | measured-lane-torch-whisper | affect/asr.py + audeering_vad.py | 16 | — | — | — | — | **Registered before re-score of L.** Install torch+transformers+faster-whisper in verityngn env; re-run measured VAD+ASR on Karp media; Fidelity should leave 0. NO_PROMOTE. |
| 2026-08-14 | T013 | live-gemini-one-karp | scripts/run_live_gemini_one.py | 15 | — | — | — | — | **Registered before live vs offline_proxy diff** on QNkPpVYagRc. No CAR peek. Confirm live_gemini True. NO_PROMOTE. |
| 2026-08-14 | T012 | signal-quality-loss-L | scripts/score_signal_quality.py | 14 | — | — | — | — | **Registered before scoring L** on n=7 Karp panel. Baseline Fidelity/NuisanceLeak/Power/ICIRnorm/DeflationGap. NO_PROMOTE. Loop keeps an iteration only if L decreases. |
| 2026-08-14 | T011 | multi-ceo-huang-nvda-catalog | docs/nvda_pre_earnings_videos.json + scripts/karp_earnings_effect.py --catalog | 13 | — | — | — | — | **Registered before multi-CEO outcome peek.** Second player catalog (Huang/NVDA) mirroring Karp schema; de-hardcoded --player-id/--catalog. CAR lookback fix (≥15d) unblocks T010 n_with_car. NO_PROMOTE. |

## Gates (must pass before PROMOTE)

| Gate | Threshold |
|------|-----------|
| ICIR | ≥ 0.40 |
| Frac IC+ | ≥ 0.55 |
| Weekly Jaccard | < 0.25 |
| Neutralization | resid ICIR ≥ 0.5 × raw |
| Cost edge | Q5−Q1 > drag @ 10 bps (hygiene) / 20 bps (promote-ready) |
| DSR | ≥ 0.95 |

## Lessons carried from hca-qngn

1. Factor PASS ≠ portfolio PROMOTE  
2. Never live-demean by sector  
3. Never `fillna(0)` on sparse alt-data  
4. Horizon must match rebalance frequency  
5. Count all trials for DSR denominator
