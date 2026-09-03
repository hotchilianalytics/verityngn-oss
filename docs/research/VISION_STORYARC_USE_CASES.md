# Vision / motion / story-arc use-cases (risk-aligned)

**Date:** 2026-08-31 (expanded from 2026-08-29)  
**Branch:** `release/v3.0.0`  
**Status:** Adaptive sampler + exhibit/brand-safety modules in OSS; full fusion deferred.

## Framing

Vision sleeves support **claim-level risk abatement** (disclosure / delivery / sponsor-readiness / legal exhibit tracking) — not lie detection, not earnings prediction.

## Adaptive sampling policy

Do **not** raise fps globally. Match sampling to scene class:

| Scene class | Typical content | fps | `media_resolution` | Token budget |
|-------------|-----------------|-----|-------------------|--------------|
| Lecture / VSL | Talking head, spoken claims | 0.2–1.0 | LOW (70 tok/frame) | Minimize |
| Motion / montage | Cuts, urgency, B-roll | 2–5 | MEDIUM | Moderate |
| Flash OCR / supers | #ad, credentials, disclaimers | 4–8 | HIGH (280 tok/frame) | Burst |
| Exhibit / slide | Deposition ELMO, earnings deck | 2–6 | HIGH on static doc frames | Targeted |

Implementation: [`verityngn/services/vision/adaptive_sampler.py`](../../verityngn/services/vision/adaptive_sampler.py) probes cut density + face coverage; wires `videoMetadata.fps` and Gemini `media_resolution`.

Google references: [video understanding](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/video-understanding), [media resolution](https://ai.google.dev/gemini-api/docs/generate-content/media-resolution).

## Prioritized use-cases (V1–V7)

| ID | Use-case | Signal | Buyer | OSS status |
|----|----------|--------|-------|------------|
| V1 | Talking-head vs B-roll ratio | Face coverage continuity, cut proxies | Agency sponsor-readiness | Stub: `story_arc.summarize_continuity` |
| V2 | Demo vs claim congruence | On-screen product/OCR vs spoken window | Brand safety / legal | Backlog (needs OCR geo) |
| V3 | Montage / urgency pacing | Cut density, loudness spikes | Disclosure / hype risk | Backlog |
| V4 | Before→after story arc | Segment clusters + “results” OCR beats | Health/finance scam pattern | Backlog |
| V5 | Lower-third / credential flash | OCR geo + short duration | Authority fabrication | Backlog |
| V6 | Exhibit tracking (depositions) | Static slide/doc frames vs speaker | Legal dossier | **`exhibit_tracker.build_exhibit_map`** |
| V7 | Synthetic media cues | Spectral AI-voice + Face Landmarker | Authenticity gate | Partial (adapters exist) |

## Vertex-native avenues (N1–N9)

| ID | Avenue | Why video/audio | Buyer | fps / res |
|----|--------|-----------------|-------|-----------|
| N1 | Earnings slide↔speech contradiction | Chart digits unspoken | IR / GC / RiskFactor upsell | 2 fps + HIGH on slides |
| N2 | Ad super / disclaimer OCR | 4-pt legal copy, flash frames | Agency legal + network QC | 6–8 fps HIGH |
| N3 | Deposition exhibit tracker | Documents not read aloud | Legal dossier | Adaptive 4–6 HIGH |
| N4 | FTC disclosure persistence | Badge duration + contrast | Agency SKU A | 8 fps on first/last 5s |
| N5 | Synthetic UGC gate | Face Landmarker + AI-voice | Brand authenticity | 2 fps + spectral |
| N6 | Before→after story arc (V4) | Results OCR beats + cut clusters | Health/finance scam / FTC | 2–4 fps + story_arc |
| N7 | Logo / watermark spoof | Persistence across cuts | Brand protection | VI LOGO + 1–2 fps |
| N8 | Audio semantic delivery-risk | Diarization, music swell, countdown | Agency + financial | Native audio 32 tok/s |
| N9 | Multi-video compare | Same claim across A-B ad cuts | Agency retainer | 1 fps LOW → HIGH on deltas |

**Park:** robotics QC, live stream, HR affect, sports, meeting-notes RAG.

## Commercial sleeves

| Sleeve | SKU | Video load-bearing when |
|--------|-----|-------------------------|
| Legal | Video claim dossier $500–1.5k/matter | Exhibit OCR, chyrons, unread document frames |
| Agency | Sponsor-readiness $1–3k/mo | Supers, #ad flash, chart-only efficacy |
| Financial | Earnings / finfluencer pre-flight | Slide↔speech mismatch |
| RiskFactor | Disclosure-Risk Audit (text MVP) | Webcast extension gated (`NO_PROMOTE`, leak < 0.20) |

## Wide scan (parked)

- Multi-speaker turn-taking / interruption as delivery-risk cue  
- Screen-share vs face camera switches (tech demos)  
- Logo / watermark persistence (brand spoofing)  
- Slow-motion / speed-ramp detection (urgency theatre)  
- Green-screen / virtual set heuristics  
- Gesture emphasis peaks aligned to contested claims  

## Explicit non-goals (this branch)

- Gemini multisense fusion / derailment-as-earnings  
- Karp / S-factor / CAR wiring  
- Employment / HR affect scoring (EU AI Act)

## Modules

- [`story_arc.py`](../../verityngn/services/vision/story_arc.py) — face-coverage continuity stub
- [`adaptive_sampler.py`](../../verityngn/services/vision/adaptive_sampler.py) — scene-class fps/res policy
- [`exhibit_tracker.py`](../../verityngn/services/vision/exhibit_tracker.py) — legal exhibit map from visual claims
- [`brand_safety_scores.py`](../../verityngn/services/report/brand_safety_scores.py) — agency visual-only flags

## Next experiments (T-ABL-004)

1. **Do not re-prove Lipozem.** Use genre seeds in [`evaluation/genre_ablation_seeds.json`](../../evaluation/genre_ablation_seeds.json).
2. Gate: visual-only share ≥ 0.25 and human rubric ≥ 0.6 on 2/3 seeds → sleeve validated.
3. Pair V1 continuity with gallery claim timestamps for congruence heatmaps.
4. Only promote V* that improve sponsor-readiness usefulness — register trials first.
