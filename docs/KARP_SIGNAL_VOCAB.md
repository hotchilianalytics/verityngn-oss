# Karp signal vocabulary

Player: `ceo_pltr_karp`. Markets-research language only — congruence / conviction / delivery-risk. **Not** a lie detector, clinical diagnosis, or employment screen (EU AI Act Art. 5(1)(f)).

Corpus (as of 2026-08-10):

| Video | Title | Venue |
|-------|-------|-------|
| `QNkPpVYagRc` | Palantir CEO Alex Karp on Israel, AI and Outlook | CNBC Davos 2024 (~14 min) |
| `dRgPbNJ5RJc` | Conversation with Alex Karp \| WEF Annual Meeting 2026 | WEF + Larry Fink (~35 min) |
| `V7mYWOzdhpc` | US software dominance, DOGE, *Technological Republic* | CNBC (pre Q1'25) |
| `ijRuuaaM6XM` | Karp + Jensen Huang NVIDIA partnership | CNBC 2025-10-28 (pre Q3'25) |
| `xe84cwQJKaE` | Seema Mody sit-down (Iran / AI) | CNBC 2026-03-12 (pre Q1'26) |
| `WBu9Ai6OX3I` | Sara Eisen sit-down | CNBC 2026-06-10 (pre Q2'26) |
| `pHu-FarYZlU` | Squawk Box Nvidia / tokens | CNBC 2026-07-01 (pre Q2'26) |

---

## Core terms

| Term | Definition |
|------|------------|
| **Player** | Longitudinal identity for one speaker (`ceo_pltr_karp`). Signals accumulate *within* player, never as cross-CEO norms. |
| **Interpreted track** | Gemini multimodal labels (emotion, arousal, valence, delivery bands, face/gesture prose). Signal tier = `interpreted`. |
| **Measured track** | Acoustic/prosodic numbers from audio (exuberance, pause ratio, shimmer, proxy VAD). Signal tier = `measured`. |
| **Fusion / fused index** | Time-aligned join of claims + affect + Gemini into `crossmodal` rows. |
| **Congruence** | 0–1 score: how aligned text, voice, and face (plus interpreted vs measured) are at a claim. High = channels agree. **Not** truth. |
| **Congruence multiplier** | Shrinks a claim’s delivery weight when channels disagree. |
| **Modality divergence** | Flag when text/voice/face disagree enough to count as a split. Rate = share of claims flagged. |
| **Delivery-risk band** | `low` / `moderate` / `high` label on congruence + z-scores. Research label only. |
| **Arousal** | 0–1 activation (calm → intense). Gemini interpreted or measured proxy. |
| **Valence** | −1…+1 pleasantness (negative → positive). |
| **Vocal emotion** | Plutchik primary: joy, trust, fear, surprise, sadness, disgust, anger, anticipation, or neutral. |
| **Delivery bands** | Discrete Gemini labels: `pace_band` (slow/moderate/fast), `pause_pattern`, `pitch_variability_band` (low/moderate/high), `disfluency_count`. |
| **Exuberance** | Measured composite of energy/pitch vs a short baseline window. High = more activated than that video’s own start. |
| **z-score (within video)** | `(x − mean_video) / std_video`. Until n≥5 videos, **not** a Karp-lifetime z. |
| **Disfluency rate** | Share of filled pauses / restarts. Today: claim-text tokens only (weak). Target: ASR word-level um/uh. |
| **Q&A reactivity delta** | Mean answer-segment arousal minus mean interviewer-question arousal. Proxy for prepared vs pressured. |
| **Topic-affect fingerprint** | Dominant emotion in geopolitics-tagged vs business-tagged windows. |
| **Tier A** | One whole-video Gemini pass → timestamped affect/delivery track. |
| **Tier B** | Short clip (±15s around high-stakes claims): spoken paraphrase, OCR, face, gesture, clip congruence. |
| **OCR chyron** | On-screen broadcast text (e.g. `PALANTIR'S KARP ON TRIP TO ISRAEL`). Used as topic evidence. |
| **prosody_proxy** | Dimensional affect estimated from energy/pause, **not** a trained VAD model. Known to under-state negative valence. |
| **n_obs** | How many videos entered the rolled value. n=1 is a seed, not a prior. |
| **NO_PROMOTE** | Trial ledger gate: do not treat as a tradable factor until hygiene gates pass. |

---

## Seed signals (S01–S10)

| ID | Name | What a move means |
|----|------|-------------------|
| **S01** | Cross-channel congruence | Channels lining up. Drift down = more split delivery. |
| **S02** | Interpreted vs measured agreement | Gemini vs microphone. Persistent valence gap may be sensor (`prosody_proxy`) not Karp. |
| **S03** | Emotional arc volatility | Arousal stdev across Tier A. High = more peaks/valleys (often Q&A). |
| **S04** | Topic-affect fingerprint | Anger-on-geopolitics vs trust-on-business is the n=1 pattern to retest. |
| **S05** | Q&A reactivity delta | Large positive = Karp answers much hotter than the question baseline. |
| **S06** | Exuberance z per claim | Which claims sit above/below that video’s own mean energy. |
| **S07** | Disfluency rate | Floor until ASR fillers exist. |
| **S08** | Pace / pitch escalation | Share of high pitch-variability segments + transitions into fast/slow. |
| **S09** | Facial–vocal–verbal alignment | Tier B Gemini clip congruence (prose face, not AUs). |
| **S10** | Conviction–claim coupling | Claim verdict × delivery-risk band. Watch TRUE + high-risk (or reverse) as corpus grows. |
| **S11** | Discourse derailment | Distance between LLM *expected* on-topic answers and Karp’s actual answer. High = topic shift / red herring / non sequitur. **Not** disinformation or deception (Krykoniuk et al. 2026). |

---

## Bands (heuristic, not calibrated)

| Quantity | low / floor | moderate / stable | high / elevated |
|----------|-------------|-------------------|-----------------|
| Congruence (S01) | < 0.55 | 0.55–0.75 | ≥ 0.75 |
| Arousal volatility (S03) | < 0.18 pstdev | — | ≥ 0.18 |
| Q&A delta (S05) | < 0.25 (“flat”) | — | ≥ 0.25 (“reactive”) |
| Derailment (S11) | < 0.25 (on-topic) | 0.25–0.45 | ≥ 0.45 (topic shift) |
| High-pitch share (S08) | < 0.20 (“calm”) | — | ≥ 0.20 (“active”) |
| S02 | `aligned` if min valence agreement ≥ 0.55 | — | `valence_gap` otherwise |

---

## What we do **not** claim

- Deception, “tells,” hidden intent, or that derailment = disinformation (the Nature paper is explicit: shifts can be malicious *or* benign).
- Cross-speaker ranking (Karp vs Cook, etc.).
- Employment / education / insurance fitness.
- That `prosody_proxy` valence is a ground-truth affect meter.
