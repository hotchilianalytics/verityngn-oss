# VerityIndex Predictions — flow + Karp panel

**For:** Derrick Horner / H1 Ventures  
**From:** VerityIndex (`verityindex-predictions`)  
**Date:** 2026-08-11  
**Status:** Live measured signals on **Alex Karp / PLTR** (n=2 videos). Multi-CEO charts from 2026-08-06 remain **synthetic**. **NO_PROMOTE.**

> Congruence / conviction / delivery-risk only. **Not** a lie detector, clinical diagnosis, or veracity judgment. Markets research — **not** for employment, HR, or education screening (EU AI Act Art. 5(1)(f)).

Companion: [H1 demo brief](H1_VENTURES_DEMO.md) · [design](PREDICTIONS_DESIGN.md) · [trials ledger](trials_ledger.md) · live HTML panel `.outputs/ceo_pltr_karp_corpus/ceo_pltr_karp_signal_report.html`

---

## 1. What we are building

Prior art (Speech Craft Analytics and related earnings-call vocal work) shows that **how** a CEO delivers Q&A can move short-horizon returns in a way that is not just text sentiment. We already extract and verify **claims** from video. Predictions adds the delivery layer and joins it, leakage-safe, to ticker outcomes.

**Wedge:** join “what was claimed and whether it checked out” to “how it was delivered” — measured audio/vision **and** Gemini’s multimodal interpretation — per speaker over time. Never a deception product.

Pilot players: Cook (AAPL), Nadella (MSFT), Huang (NVDA), **Karp (PLTR)**, Musk (TSLA; xAI/SpaceX/X untradable). Karp is first live subject: high-variance interviews, strong vision track, dense CNBC/WEF archive.

---

## 2. Feature flow (one video → player time series)

```
YouTube / earnings video
        │
        ├─ Claims pipeline (existing VerityIndex)
        │     Vertex Gemini multimodal → factual claims
        │     counter-intel + web verify → TRUE / FALSE / UNCERTAIN
        │     {video_id}_report.json
        │
        └─ Multi-sense sleeve  (MULTISENSE_ENABLED=1)
              ├─ Interpreted (Gemini)
              │     Tier A: whole-video affect / delivery track (~15–45s segments)
              │     Tier B: claim ±15s clips (face / gesture / OCR / clip congruence)
              └─ Measured (ffmpeg → 16 kHz WAV)
                    F0, energy, pause, shimmer, exuberance vs video baseline
                    VAD: prosody_proxy today (audEERING weights not loaded)
              │
              ▼
        Fusion  (align + crossmodal + Plutchik arcs)
              congruence, modality_divergence, delivery_risk_band
              interpreted × measured agreement
              {video_id}_fused_index.json
              │
              ▼
        Player registry  ceo_pltr_karp
              S01–S11 rollup (within Karp, never vs Cook/Huang)
              │
              ▼
        Event study  (features as-of video date t only)
              next earnings print after t → surprise / CAR H=1,5,10,21,30
              trials ledger row registered BEFORE peeking returns
```

Authenticity gate (deepfake / rPPG consistency) sits in front of affect for production; Karp research runs assume public broadcast video.

**Two tracks, always labeled**

| Track | What it is | Failure mode we watch |
|-------|------------|------------------------|
| **Measured** | Open numbers from the waveform | `prosody_proxy` valence is mildly positive even when Gemini is angry → S02 `valence_gap` |
| **Interpreted** | Gemini labels (`signal_tier: interpreted`) | Different cues than a human annotator (same issue the 2026 derailment paper reports) |

Disagreement is a **feature** (modality divergence), not something we average away.

---

## 3. What each module actually emits

| Module | Path | Output |
|--------|------|--------|
| Claims | `workflows/pipeline.py` | Verified claims + timestamps |
| Affect | `services/affect/` | Exuberance, pause, disfluency (text-token until ASR) |
| Gemini multi-sense | `services/fusion/gemini_multisense.py` | Tier A/B JSON |
| Derailment (S11) | `services/fusion/derailment.py` | Expected-vs-actual Q&A distance |
| Fusion | `services/fusion/crossmodal.py` | Congruence / delivery-risk |
| Players | `services/players/` | Person ↔ ticker; untradable entities stay mediasphere-only |
| Mediasphere | `services/mediasphere/` | Appearance velocity (Musk is the stress test) |
| Timeseries | `services/timeseries/` | PIT features, earnings join, CAR |
| Quant gates | hca-qngn hygiene | ICIR ≥ 0.40, frac IC+ ≥ 0.55, Jaccard < 0.25, DSR ≥ 0.95 |

Vendor sleeves (millionways, Corsound, Nemesysco, Revealense) are **optional, labeled** (`source: vendor:…`). They never overwrite Tier-1 fields.

---

## 4. Karp signal registry (S01–S11)

Longitudinal **within Karp**. n=1 is a seed; rolling z needs ≥5 videos. Bands are heuristic, not calibrated.

| ID | Name | Read as |
|----|------|---------|
| S01 | Cross-channel congruence | Text / voice / face lining up. Drift down = split delivery. **Not** truth. |
| S02 | Interpreted vs measured agreement | Gemini vs microphone. Persistent valence gap may be the sensor. |
| S03 | Emotional-arc volatility | Arousal stdev across Tier A. Interviews usually > prepared talks. |
| S04 | Topic–affect fingerprint | Dominant emotion on geopolitics vs business windows. |
| S05 | Q&A reactivity delta | Answer arousal − question arousal. Proxy for prepared vs pressured. |
| S06 | Exuberance z | Claim energy vs **that video’s** mean (not yet a Karp-lifetime z). |
| S07 | Disfluency rate | Floor until ASR um/uh. |
| S08 | Pace / pitch escalation | Share of high pitch-variability + transitions into fast/slow. |
| S09 | Face–voice–verbal (Tier B) | Observational clip congruence (prose face, not FACS AUs). |
| S10 | Conviction–claim coupling | Verdict × delivery-risk. Watch TRUE + high-risk (or reverse). |
| **S11** | **Discourse derailment** | [Krykoniuk, Hopkin-King & Roberts 2026](https://www.nature.com/articles/s41599-026-07900-x): LLM *expected* on-topic answers vs actual answer. High = topic shift / red herring / non sequitur. **Not** disinformation. Paper: ~77% vs humans, **different cues / bias**; derailment can be malicious or benign. |

---

## 5. Hygiene (same as the fund book)

- Features at time *t* use only information available at *t*.
- Pre-print interviews only for an earnings test. On-print webcasts and next-day victory laps are labeled and **excluded** from T010.
- Register the trial **before** looking at CAR (`docs/trials_ledger.md`).
- Factor PASS ≠ portfolio PROMOTE. No `fillna(0)` on sparse alt-data. Horizon must match rebalance.

---

## 6. Latest Karp results panel (measured, 2026-08-11)

**Corpus n=2 · trial T009 · NO_PROMOTE**  
Live Gemini on both videos. Affect is still `prosody_proxy` (no audEERING VAD, no AUs).

| Video | Venue | Claims | S01 congruence | S05 Q&A Δ | S11 derailment |
|-------|--------|-------:|---------------:|----------:|---------------:|
| [QNkPpVYagRc](https://www.youtube.com/watch?v=QNkPpVYagRc) | CNBC Davos 2024 (~14 min) | 5 | **0.71** moderate | **+0.30** reactive | **0.80** high (5 pairs, Gemini) |
| [dRgPbNJ5RJc](https://www.youtube.com/watch?v=dRgPbNJ5RJc) | WEF 2026 + Fink (~35 min) | 6 | **0.89** high | **−0.01** flat | *no usable Q/A text pairs* |

**Rolled (unweighted mean where numeric)**

| Signal | Corpus | Band | Note |
|--------|--------|------|------|
| S01 congruence | **0.80** | high | Range 0.71–0.89; delivery-risk **low** on both; divergence rate 0 |
| S02 interp×measured | 0.81 | **valence_gap** | Arousal agrees; valence does not (proxy sensor) |
| S03 arousal pstdev | 0.13 | stable | CNBC 0.20 (elevated) vs WEF 0.06 (flat long-form) |
| S04 topic–affect | split | — | CNBC: geopolitics **anger** vs business **neutral**. WEF: both **neutral** |
| S05 Q&A Δ | 0.14 | flat | Average hides the CNBC spike; do not use the mean alone |
| S08 high-pitch share | 0.24 / 0.06 | active vs calm | CNBC more “on”; WEF quieter |
| S09 Tier B alignment | 0.89 | high | Gemini prose face, not FACS |
| S10 coupling | all low delivery-risk | — | No TRUE+high-risk cell yet |
| S11 derailment | 0.80 on CNBC only | high | WEF unscored (not enough spoken/claim text on question turns) |

**How to read this (and how not to)**

- CNBC is a **reactive interview** (hot answers, geopolitics anger, topic-shift on Q&A). WEF is a **prepared conversation** (high congruence, flat Q&A, no derailment score). That split is the point of a player prior: venue matters.
- S11 = “did the answer stay on the question’s topic?” It is **not** “is Karp lying” and **not** “is this disinfo.”
- S02 valence_gap is a **known instrument issue** until real VAD is on. Do not sell it as Karp-specific.
- n=2 is a seed. No Karp-lifetime z, no promote, no feed.

HTML / JSON: `.outputs/ceo_pltr_karp_corpus/ceo_pltr_karp_signal_report.{html,json,md}`

---

## 7. Earnings test (T010) — registered, not yet reported

**Hypothesis (pre-registered):** pre-print S01 / S05 / S11 associate with the **next** PLTR print’s raw CAR H=1.

**In flight (claims + multi-sense), pre-print only:**

| Video | Recorded | Maps to print |
|-------|----------|----------------|
| `V7mYWOzdhpc` CNBC book / DOGE | ~Feb 2025 | Q1'25 2025-05-05 |
| `ijRuuaaM6XM` Karp + Huang | 2025-10-28 | Q3'25 2025-11-03 |
| `xe84cwQJKaE` Seema Mody | 2026-03-12 | Q1'26 2026-05-04 |
| `WBu9Ai6OX3I` Sara Eisen | 2026-06-10 | Q2'26 2026-08-03 |
| `pHu-FarYZlU` Squawk / tokens | 2026-07-01 | Q2'26 2026-08-03 |

WEF 2026-01-20 already in corpus → Q4'25 2026-02-02. Davos 2024 stays in the signal corpus, **not** in the 2025–26 event study.

**Excluded on purpose:** Q3'25 webcast; 2025-11-04 Squawk (post-print); 2026-08-03 Seema Mody (print day).

Jun + Jul 2026 share one print → n_events < n_videos. Even at n≈5 the honest label is **underpowered**. We will report Spearman and a verdict of `no_reliable_earnings_effect` or `association_present_underpowered` — never alpha.

---

## 8. What “done” looks like before we talk promote

1. ≥5 Karp videos with live Gemini **and** measured VAD/AU (not only `prosody_proxy`).
2. T010 complete, leakage-safe, n_events large enough that ICIR / DSR are defined.
3. Per-speaker z, not cross-CEO ranks.
4. Product copy still: congruence / conviction / delivery-risk. No lie-detector language in the feed, the UI, or a pitch deck.

Until then the live Karp panel is a **methods + instrumentation proof** on the first pilot CEO, sitting next to the synthetic five-CEO layout from 6 Aug.
