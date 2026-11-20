# Opt-In (Non-Default) Sophisticated Media Paths — VerityNgn 3.0.1

**Audience:** NotebookLM, technical readers, IR / brand reviewers evaluating advanced sleeves  
**Package lock:** `verityngn==3.0.1` · Launch day **Monday, Nov 16, 2026**  
**Rule:** These paths **ship in the wheel** but are **not** what `verityngn analyze` does by default. Do not pitch them as live-on-every-run until 3.1 / 3.2 turns the relevant pieces default-on.

---

## Capability boundary (three layers)

| Layer | Status in 3.0.1 | What a reviewer sees |
|-------|-----------------|----------------------|
| **A — Live default** | On every full run | Adaptive 1–6 fps · pixel claims · `brand_safety_scores.json` · `{id}_exhibit_map.json` · Deep Research `visual_only_claims` |
| **B — Opt-in sleeves (this doc)** | In wheel; flags / extras required | MediaPipe · librosa/VAD · MultiSense S00–S15 · AGENTIC frame search · AuthenticityGate · `--story-arc` |
| **C — Futures default-on** | Research roadmap | **3.1** object/action semantics + visual–spoken contradiction · **3.2** pose/lip/face/audio congruence promoted from Layer B |

NotebookLM should treat Layer B as “sophisticated paths available today for research operators,” and Layer C as “what becomes product-default next.”

---

## Install the sleeves

```bash
pip install 'verityngn[deep,vision,audio,predictions]==3.0.1'
```

Extras map:

| Extra | Pulls in |
|-------|----------|
| `[vision]` | MediaPipe Face Landmarker, blendshapes, HFAsy_proxy helpers, story-arc continuity |
| `[audio]` | Librosa prosody / exuberance / spectral TTS cues, VAD hooks |
| `[predictions]` | MultiSense fusion, S00–S15 registry scripts, fused index writers |
| `[deep]` | Deep Research (already recommended for gallery-quality runs) |

---

## Path 1 — Vision landmarks & story-arc (`verityngn[vision]`)

**Enable**

```bash
verityngn analyze --tier full --deep --story-arc '<url-or-file>'
# MediaPipe Face Landmarker used when vision extra + local frames available
```

**What it measures (not lie detection)**

| Signal | Spec | Use |
|--------|------|-----|
| 478 3D face landmarks | MediaPipe Face Landmarker | Pose / head stability over time |
| 52 ARKit-style blendshapes | Explicit L/R | Blink, gaze-from-blendshape, expression intensity |
| `HFAsy_proxy` (S12 on-ramp) | L1 of L vs R blendshapes over time | Banker et al. (*Mgmt Sci* 2024) hemifacial asymmetry **proxy** — not their CNN HFAsy |
| `--story-arc` / continuity JSON | Change-point over fused affect | Spot Runner–style emotional-arc indexing (`sr_*` Plutchik leaves) |

**Honest limits:** Blendshapes ≠ OpenFace FACS AUs. `HFAsy_proxy` is a research on-ramp, not a published Banker replication. Employment / hiring use is out of scope (EU AI Act Art. 5(1)(f) posture).

**Futures link:** These measurements become the calibrated **3.2** default-on pose/lip/face congruence track.

---

## Path 2 — Audio affect & synthetic-voice cues (`verityngn[audio]`)

**Enable:** install `[audio]`; operators run affect / prosody extractors on local audio (see `docs/predictions/` and `scripts/predictions/`).

| Cue family | Examples | Risk framing |
|------------|----------|--------------|
| Prosody / pace / pitch | Qin & Yang (2019) escalation (`S08`) | Delivery / conviction change mid-segment |
| Vocal Q&A reactivity | Mayew & Venkatachalam (2012) (`S05`) | Scrutiny response in live Q&A |
| VAD / diarization hooks | Speaker turns | Within-speaker baselines (`SpeakerBaseline`) |
| Spectral TTS / synthetic indicators | AI-voice suspicion flags | Provenance / authenticity adjacent — not “deepfake conviction” |

**Hygiene:** Near-chance vocal dissonance (`S14`) stays **refused**. No synthetic `0.5` fills that leak `n_claims`.

**Futures link:** Librosa + VAD feed **3.2** cross-modal audio congruence with pose/lip.

---

## Path 3 — MultiSense Tier A/B + S00–S15 (`verityngn[predictions]` + env)

**Enable**

```bash
export MULTISENSE_ENABLED=1
# CI / no credentials:
# export MULTISENSE_OFFLINE=1
verityngn analyze --tier full --deep '<ceo-or-keynote-url>'
```

**What it writes (when enabled)**

- `{video_id}_multisense.json` — Tier A/B clip congruence measurements  
- Refreshed `_affect.json`  
- `_fused_index.json` — cross-modal fused rows + story arcs  

**Registry snapshot (delivery / instrument risk — not alpha)**

| ID | Theme | Status posture |
|----|-------|----------------|
| S00 | Provenance / AuthenticityGate | Fail-closed before behavioral scoring |
| S01 | Oxford-Man style cross-modal distance | Pose↔audio distance |
| S05 | Vocal Q&A reactivity | Live interview scrutiny |
| S08 | Pace / pitch escalation | Conviction / stress cues |
| S11 | Q&A discourse derailment (Krykoniuk) | Topic drift under pressure |
| S12 | HFAsy_proxy | Hemifacial asymmetry proxy |
| S13 | Expression–news incongruence | Blankespoor-style mismatch |
| S14 | Vocal dissonance | **REFUSE** near-chance |
| S15 | Disclosure / filing vs spoken | Bridge to ClearFactor / rfkit |

Full rating table: `docs/predictions/VIDEO_CUE_CRITICAL_RATING.md` · registry: `docs/predictions/RISK_FACTOR_REGISTRY_S00_S15.md`.

**Futures link:** MultiSense is the measurement spine that **3.2** promotes from opt-in sleeve → default delivery-and-conviction track.

---

## Path 4 — Gemini AGENTIC video search (`VN_AGENTIC_VIDEO=1`)

**Enable**

```bash
export VN_AGENTIC_VIDEO=1
verityngn analyze --tier full --deep '<url>'
```

**What it does:** Spike path that requests Gemini `mediaProcessing=AGENTIC` (frame search / tool-like video understanding) before or beside the standard segmented Vertex path.

**Why it matters for futures:** AGENTIC frame search is the intended accelerator for **3.1 object / prop / action semantics** — finding product demos, before/after lighting, timelapse, crowd/venue framing that today’s OCR-biased prompts under-extract (only **4/81** `demonstration` claims in the v3 benchmark).

**Honest limits:** Still an **opt-in spike** in 3.0.1. Keep off production Batch pins until a dedicated ablation says otherwise (`docs/research/GEMINI_2026_CAPABILITY_GAP.md`).

---

## Path 5 — AuthenticityGate (fail-closed provenance)

**Role:** C2PA / CorSound / rPPG-style adapters that **block or flag** behavioral scoring when provenance is weak (`S00`).

**Posture:** Fail-closed. Behavioral / congruence scores must not run “as if authentic” when the gate fails. This stays fail-closed in 3.1/3.2 — it is not a marketing feature that “detects fakes for you.”

---

## Operator recipe card (research run)

```bash
pip install 'verityngn[deep,vision,audio,predictions]==3.0.1'

export MULTISENSE_ENABLED=1
# optional research spikes:
# export VN_AGENTIC_VIDEO=1

verityngn analyze --tier full --deep --story-arc \
  'https://www.youtube.com/watch?v=lb_ZJylekWo' \
  -o outputs/notebooklm_ceo_sleeve_demo
```

**Expect default artifacts:** `report.html`, `deep.html`, `brand_safety_scores.json`, `{id}_exhibit_map.json`  
**Expect sleeve artifacts (when enabled):** `_multisense.json`, `_affect.json`, `_fused_index.json`, story-arc / continuity JSON  

**Do not claim:** employment fitness, earnings alpha, or that congruence ran on every gallery report without the flags above.

---

## How Layer B becomes Layer C

| Opt-in path today | Turns default-on | Product language |
|-------------------|------------------|------------------|
| OCR/pixel + brand-safety (already default) | — | Visual text / exhibits & brand-safety |
| AGENTIC + prompt expansion | **3.1** | Object / action semantics; visual–spoken contradiction; splice risk |
| MediaPipe + MultiSense + librosa/VAD | **3.2** | Pose / lip / face / audio congruence (delivery / conviction / disclosure) |

Companion brief: [`MULTIMODAL_AND_FUTURES_v3.md`](MULTIMODAL_AND_FUTURES_v3.md).
