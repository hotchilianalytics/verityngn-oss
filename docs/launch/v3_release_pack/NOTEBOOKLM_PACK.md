# NotebookLM source pack — VerityNgn OSS 3.0.1

**Upload this folder (or the zip) into a single Google NotebookLM notebook.**  
**Package:** `verityngn==3.0.1` on PyPI (`3.0.0` yanked) · **Launch:** Monday, Nov 16, 2026 · Engine tip `1b2cca8`

This pack is built so NotebookLM can answer three different questions without conflating them:

1. **What is live default-on today?** (pixel risk, brand-safety, exhibits, Deep Research)  
2. **What sophisticated media analysis already ships but is opt-in / non-default?** (MediaPipe, MultiSense, audio, AGENTIC, AuthenticityGate)  
3. **Where does research go next?** (3.1 object/action + visual–spoken contradiction; 3.2 pose/lip/audio congruence)

---

## Suggested source order (add in this order)

| # | File | Role in the notebook |
|---|------|----------------------|
| 1 | **NOTEBOOKLM_PACK.md** (this file) | Orientation + ask prompts |
| 2 | **MULTIMODAL_AND_FUTURES_v3.md** | Live proof numbers + 3.1/3.2 roadmap |
| 3 | **OPTIN_MEDIA_PATHS_v3.md** | Non-default sophisticated sleeves (flags, extras, hygiene) |
| 4 | **EXEC_SUMMARY_v3.md** | One-page exec lock |
| 5 | **WHITE_PAPER_ONE_PAGER.md** | Problem → platform morph |
| 6 | **RELEASE_NOTES_v3.0.1.md** | Install lock + what 3.0.1 actually is |
| 7 | **EXAMPLES.md** | Copy-paste Lipozem / SB1507 / CEO fixtures |
| 8 | **BLOG_POST.md** | Public narrative (features + futures section) |
| 9 | **verityngn_oss_v3_release.pdf** | Release paper (§2 multimodal now, §8 futures) |
| 10 | **VerityNgn_3_Release_with_examples.pdf** *(zip root)* | Deck incl. slide **12D** Now → Futures |
| 11 | **VerityNgn_3_example_slides.pdf** *(zip root)* | 08A + 12A–12D only |
| 12 | Figures PNGs in this folder | Gallery / platform visuals for Studio |

Optional social drafts (`HN_POST`, `X_THREAD`, `LINKEDIN_POST`, `SURFACES`) are secondary — useful for tone, not for capability truth.

---

## Hard capability rules (paste into NotebookLM custom instructions if available)

```
VerityNgn 3.0.1 capability boundary:
- DEFAULT-ON: adaptive 1–6 fps, pixel claims (visual_text/graphic/chart/demonstration),
  brand_safety_scores.json, {id}_exhibit_map.json, Deep Research visual_only_claims.
- OPT-IN (in wheel, NOT default): verityngn[vision|audio|predictions], MULTISENSE_ENABLED=1,
  VN_AGENTIC_VIDEO=1, AuthenticityGate, --story-arc. Never say these ran on every gallery report.
- FUTURES: 3.1 = object/action semantics + visual–spoken contradiction; 3.2 = pose/lip/face/audio
  congruence default-on. Framing = delivery/conviction/disclosure risk — NEVER lie detection,
  NEVER earnings alpha, NEVER employment screening.
- Install: pip install 'verityngn[deep]==3.0.1' — do not recommend ==3.0.0 (yanked).
- Proof anchors: 81 pixel-only claims; 18/40 (45%) on SB1507; 5 Lipozem silent credential cards.
```

---

## Starter questions to ask NotebookLM

### Live multimodal (Layer A)

- Summarize what VerityNgn 3.0.1 extracts from pixels by default, with the SB1507 and Lipozem proof numbers.
- Explain `brand_safety_scores.json` and `{video_id}_exhibit_map.json` as auto-emitted sidecars.
- Why do transcript-only tools miss 45% of the SB1507 binder?

### Opt-in sophisticated paths (Layer B)

- List every non-default media sleeve in 3.0.1 and the exact install/env flag to turn it on.
- What does MediaPipe measure (landmarks, blendshapes, HFAsy_proxy), and what must we *not* claim?
- How does MultiSense (`MULTISENSE_ENABLED=1`) relate to S00–S15, and which sensor is refused (S14)?
- What is `VN_AGENTIC_VIDEO=1` for, and how does it connect to 3.1 object/action semantics?
- Draft an operator recipe that enables vision + audio + predictions sleeves for a CEO talking-head.

### Futures (Layer C)

- Produce a 3.0.1 → 3.1 → 3.2 roadmap slide in prose, separating live / opt-in / future.
- How do Spot Runner, Mayew, Banker HFAsy, Krykoniuk, and Kim disclosure merge into the 3.2 congruence track?
- Why are only 4/81 benchmark claims typed `demonstration`, and what research closes that gap?

### Honest product language

- Rewrite a launch blurb that never calls VerityNgn a lie detector and never implies congruence is default-on.
- Contrast Predictions/RiskFactor sensors (OSS) vs ClearFactor disclosure services (paid).

---

## One-paragraph pitch (Studio / Audio Overview seed)

VerityNgn 3.0.1 is an Apache multimodal claim-risk engine on PyPI: adaptive 1–6 fps sampling, eighty-one verified pixel-only claims in the release benchmark, forty-five percent of SB1507 claims from slides and charts alone, and auto-emitted brand-safety and exhibit JSON on every full run. Sophisticated media paths — MediaPipe landmarks and blendshapes, librosa prosody, MultiSense S00–S15, Gemini AGENTIC frame search, and a fail-closed AuthenticityGate — already ship in the same wheel as opt-in sleeves for research operators. The roadmap turns object and action semantics plus visual–spoken contradiction default-on in 3.1, then pose, lip, face, and audio congruence default-on in 3.2, framed strictly as delivery, conviction, and disclosure risk — never lie detection.

---

## Zip layout

```
verityngn_v3_release_pack_3.0.1.zip
├── v3_release_pack/          ← upload this folder to NotebookLM
│   ├── NOTEBOOKLM_PACK.md    ← start here
│   ├── MULTIMODAL_AND_FUTURES_v3.md
│   ├── OPTIN_MEDIA_PATHS_v3.md
│   ├── EXEC_SUMMARY_v3.md
│   ├── WHITE_PAPER_ONE_PAGER.md
│   ├── RELEASE_NOTES_v3.0.1.md
│   ├── EXAMPLES.md
│   ├── BLOG_POST.md
│   ├── verityngn_oss_v3_release.pdf
│   └── …figures + social drafts…
├── VerityNgn_3_Release_with_examples.pdf
├── VerityNgn_3_example_slides.pdf
├── verityngn_oss_v3_release.pdf
├── RELEASE_NOTES_v3.0.1.md
└── EXEC_SUMMARY_v3.md
```

Rebuild locally:

```bash
# from repo root after editing pack sources
zip -r ~/Downloads/verityngn_v3_release_pack_3.0.1.zip docs/launch/v3_release_pack \
  -x '*/.DS_Store'
zip -j ~/Downloads/verityngn_v3_release_pack_3.0.1.zip \
  papers/verityngn_oss_v3_release.pdf \
  docs/launch/decks/VerityNgn_3_Release_with_examples.pdf \
  docs/launch/decks/VerityNgn_3_example_slides.pdf \
  docs/launch/RELEASE_NOTES_v3.0.1.md \
  docs/launch/EXEC_SUMMARY_v3.md
```
