# VerityNgn 3.0: an open claim-risk engine you can run on a video

**Release:** OSS **3.0.1** · Apache-2.0 · on [PyPI](https://pypi.org/project/verityngn/3.0.1/) · engine tip `1b2cca8` · docs tip `f6aeb2e`  
**CTA:** [PyPI](https://pypi.org/project/verityngn/3.0.1/) · [gallery](https://verityindex.com/gallery) · `pip install 'verityngn[deep]==3.0.1'`

Take a YouTube URL or a local file. Get a claim-level **risk** report: what was said, what the pixels showed, what independent sources contradict, and what residual risk remains if someone acts on it.

That is VerityNgn 3.0. It is not a lie detector, not an earnings model, and not a crawl of the open web. It is a multimodal engine — extract, classify, verify, report — and the open core of a small risk platform.

---

## The job

Transcript-only checkers miss on-screen graphics. Naive web search often retrieves the subject’s own press as “evidence.” A single TRUE/FALSE ladder mashes a Senate vote together with a modeled forecast and a “in my view.”

VerityNgn 3.0 splits those problems:

1. **See the video**, not just the captions.
2. **Type the claim** (fact, inference, causal argument, opinion, prediction, thin assertion).
3. **Look for contradiction** on purpose — counter-intelligence, not confirmation.
4. **Hand a reviewer an action**, not a moral score.

```mermaid
flowchart LR
  in["YouTube URL or local file"] --> extract["Extract<br/>speech · OCR · frames"]
  extract --> kinds["Classify<br/>six claim kinds"]
  kinds --> verify["Verify<br/>counter-intel + sources"]
  verify --> report["Report<br/>CRAAP or SIFT · HTML/MD/JSON/PDF"]
  report --> deep["Optional Deep Research"]
```

---

## Features and benefits

| Feature | What it is | Benefit |
|---------|------------|---------|
| **Adaptive 1–6 fps multimodal extract** | Content-aware sampling + speech, OCR, charts, exhibits — not transcript-only | You catch claims that live on a slide or a supers, not only in the VO |
| **Pixel claim proof (v3.0.1)** | 81 verified pixel-only claims across 10 release runs; **18/40 (45%)** on SB1507; silent Lipozem credential cards | Transcript-only would miss nearly half an analyst binder and every silent testimonial card |
| **Visual risk sidecars** | `brand_safety_scores.json` + `{id}_exhibit_map.json` auto-emitted on full runs | Brand/sponsor teams get visual-only high-risk, credential-flash, and blink-disclosure counts |
| **Six claim kinds** | Fact, data-derived inference, causal/analytical, reasoned opinion, prediction, unverified assertion | A forecast is not “false because it hasn’t happened”; an opinion is not scored as a fact |
| **Counter-intelligence** | Actively search for contradictory reviews; down-weight press-release-shaped sources | You do not treat the subject’s own PR as independent confirmation |
| **Genre-aware §9** | Consumer videos → CRAAP. Analyst videos → SIFT + risk chips | The method review matches the genre instead of forcing one rubric |
| **Analysis tiers** | `light` / `full` / `local-light` / `local-full` | Triage in minutes, or a full diligence pass, without a second product |
| **Deep Research (`--deep`)** | Grounded forensic brief with a `visual_only_claims` lead | A second model stresses cites — including pixel-only risk — without a closed “pro” fork |
| **Captions CLI** | `verityngn captions <url>` | Operators can see whether VTT actually arrived (YouTube Data API metadata is not a caption download) |
| **Open-core engine** | Apache-2.0 CLI + optional `verityngn[vision,audio,predictions]` sleeves | Research quality lives in OSS; hosted credits and apps sit on verityindex.com |

![Six claim kinds](../blog/assets/verityngn-claim-classification-diagram.png)

*Figure. Six claim kinds. Source-backed facts stay on a true/false ladder. Everything else carries likelihood, evidence confidence, and residual reliance risk — not one mashed score.*

---

## How a run is routed

```mermaid
flowchart TB
  start["verityngn analyze --tier auto"] --> genre{"Claim mix"}
  genre -->|"mostly checkable facts"| craap["Consumer pack<br/>TRUE/FALSE ladder<br/>§9 CRAAP"]
  genre -->|"data-derived / causal / predictive"| sift["Analyst pack<br/>typed sections + risk chips<br/>§9 SIFT"]
  craap --> out["HTML · Markdown · JSON · PDF"]
  sift --> out
  out --> opt["Optional --deep forensic brief"]
```

| Tier | Command | When to use |
|------|---------|-------------|
| **light** | `verityngn analyze --tier light <url>` | Fast YouTube triage |
| **full** | `verityngn analyze --tier full <url> --deep` | Diligence / gallery |
| **local-light** | `verityngn analyze --tier local-light -f clip.mp4` | File transcript → short brief |
| **local-full** | `verityngn analyze --tier local-full -f clip.mp4` | Matter upload, full report |

Consumer example: Lipozem (`tLJC8hkK-ao`) stays on the classic ladder with CRAAP and a Deep Research pass.

Analyst example: a legislative / quantitative video routes into typed sections. Section 9 becomes Stop / Investigate / Find better coverage / Trace — SIFT — instead of CRAAP.

---

## Applications

Same engine. Different **domain packs**: inputs, claim typology, §9 method, and the action you hand a human.

```mermaid
flowchart TB
  engine["L1 OSS engine"]
  engine --> c["Consumer / VSL<br/>sponsor-readiness"]
  engine --> a["Analyst / legislative<br/>method review"]
  engine --> e["CEO interview<br/>delivery sensors"]
  engine --> l["Legal deposition<br/>spoken record"]
  engine --> h["Health / lab<br/>counter-intel"]
  engine --> d["Disclosure<br/>Item 1A vs own 8-K"]
```

| Application | Who | What v3.0.1 gives them | Proven on |
|-------------|-----|------------------------|-----------|
| **Sponsor-readiness** | Agencies, brands | Claim-level review of a promotional video before money attaches | Lipozem — primary-10 battery **39** claims; Monday commercial smoke **37** claims (same video, later pin) · CRAAP |
| **Analyst method review** | Creators who sell analysis | Typed claims + SIFT so a modeled number is not treated as a news fact | SB1507 local scorecard **40** claims (Chris-approved report; source mp4 not in git) |
| **CEO interview risk** | IR, boards, journalists | What was said on camera, timestamped, against the public record | Karp / Huang / Nadella battery |
| **Deposition / legal spoken** | Counsel, experts | Structured claims from testimony, not a transcript dump | Butler Kahn, 39 claims |
| **Health counter-intel** | Reviewers of contested lab / peptide claims | Contradictory sources sought on purpose | Carney Peptides, 40 claims |
| **Disclosure (paid app)** | GC / disclosure committee | Hedged Item 1A next to the company’s own dated admission | ClearFactor / rfkit sleeve — not the default Batch image |

Hosted gallery and credits live on [verityindex.com](https://verityindex.com). The engine quality path is the same Apache tree.

---

## Proof: primary-10 battery

Ten videos. Every row extracted claims. One documented swap (Huang Squawk replaced a 12-hour LIVE restream that died mid-job). Not a leaderboard. A coverage matrix.

**Claim counts below are the primary-10 battery run** (`docs/launch/BATTERY_RESULTS_v3.md`). A later Cloud Run / Batch pin of the same Lipozem URL (`tLJC8hkK-ao`, 2026-11-08 smoke) returned **37** claims — label the run when you cite a number.

```mermaid
xychart-beta
    title "Claims extracted — primary-10 battery"
    x-axis ["Lipozem", "SB1507", "Karp CNBC", "Dual-CEO", "Huang", "Karp WEF", "Nadella", "Odd Lots", "Deposition", "Peptides"]
    y-axis "Claims" 0 --> 45
    bar [39, 40, 37, 32, 16, 40, 19, 40, 39, 40]
```

![Gallery claims per video](../papers/figures/gallery_live_claims_per_video.png)

| Lane | Videos | Claims (this battery) |
|------|--------|------------------------|
| Consumer / health | Lipozem, Carney | 39 + 40 |
| Analyst | SB1507 | 40 |
| CEO interview | Karp ×3, Huang, Nadella | 37 + 32 + 16 + 40 + 19 |
| Finance podcast | Odd Lots | 40 |
| Legal spoken | Butler Kahn | 39 |
| **Live rows 3–10** | | **263** |

Full table: [BATTERY_RESULTS_v3.md](BATTERY_RESULTS_v3.md).

---

## Open core, not a closed quality fork

```mermaid
flowchart TB
  subgraph oss ["Apache OSS — verityngn-oss"]
    l1["Engine: extract · classify · verify · DR"]
    l2["Sleeves: CRAAP · SIFT · CEO sensors · brand safety"]
    l3["Agent: CLI now · MCP / skills in 3.1"]
  end
  subgraph hosted ["Hosted — verityindex.com"]
    l4["Control plane: runs, gallery, billing, BYOC"]
    l5["Apps: ClearFactor disclosure review, sponsor packs"]
  end
  oss --> hosted
```

![Open-core architecture](../papers/figures/open_core_architecture.png)

If verification, Deep Research, or the claim typology lived only behind a paywall, the open-core story would be a lie. Those stay in OSS. What you pay for is hosted scale, credits, a gallery, and counsel-side services (vault, engagement, calendar) — not a better engine.

Two names that must not be mashed together:

1. **Predictions / CEO sensors (S00–S15)** — optional OSS extra `verityngn[predictions]`. Delivery / instrument measurement. Not allocation alpha.
2. **ClearFactor disclosure review** — Item 1A hedge vs the company’s own 8-K. Paid app on the same claim/evidence pattern.

---

## Try it

```bash
pip install 'verityngn[deep]==3.0.1'
verityngn analyze --tier light 'https://www.youtube.com/watch?v=tLJC8hkK-ao'
verityngn analyze --tier full 'https://www.youtube.com/watch?v=VIDEO_ID' --deep
verityngn captions 'https://www.youtube.com/watch?v=VIDEO_ID'
# Analyst local-file path (mp4 you already have):
# verityngn analyze --tier local-full -f /path/to/clip.mp4 --deep
```

Gemini / Vertex credentials are required for the LLM path. `VERTEX_LOCATION=global` for current Vertex models. Cookies for yt-dlp when YouTube blocks anonymous caption fetch. Prefer **`3.0.1`** (do not pin yanked `3.0.0`).

Public gallery: [verityindex.com/gallery](https://verityindex.com/gallery). Examples: [EXAMPLES.md](EXAMPLES.md). Notes: [RELEASE_NOTES_v3.0.1.md](RELEASE_NOTES_v3.0.1.md).

---

## Where the research goes next (3.1 / 3.2)

**Live today:** Visual Text / Exhibits & Brand-Safety — adaptive 1–6 fps, four pixel modalities, `brand_safety_scores.json`, exhibit maps.

**Honest gap:** early prompts catch slides/OCR (77/81) more than physical demos (4/81). That under-extraction is the 3.1 job.

| Release | Turning default-on |
|---------|-------------------|
| **3.1** | Object / prop / action semantics; visual–spoken contradiction; temporal splice risk |
| **3.2** | Pose / lip / face / audio congruence atop MediaPipe + MultiSense + librosa sleeves already in the wheel |

Heritage merging into that track: Spot Runner arcs, Speech Craft / Mayew vocal Q&A, Banker HFAsy, Krykoniuk derailment, Kim disclosure → ClearFactor — plus negative-result hygiene (refuse near-chance S14; no synthetic vision fills). Framed as **delivery / conviction / disclosure risk**, never lie detection.

Full brief: [MULTIMODAL_AND_FUTURES_v3.md](v3_release_pack/MULTIMODAL_AND_FUTURES_v3.md).

---

## What we do not claim

- Not a lie detector and not a single “truthfulness” score.
- Not earnings prediction or portfolio alpha.
- Not an open-web, podcast, or social crawler.
- English-first. YouTube + local file; not TikTok-native.
- LLM-assisted briefs still need a human. If a report looks wrong, the video id is the bug report.
- Opt-in MediaPipe / MultiSense congruence is **in the 3.0.1 wheel** but not default-on until 3.2.

---

## Read next

- Multimodal + futures: [MULTIMODAL_AND_FUTURES_v3.md](v3_release_pack/MULTIMODAL_AND_FUTURES_v3.md)
- Platform layers: [PLATFORM_OVERVIEW.md](../platform/PLATFORM_OVERVIEW.md)
- Domain packs: [DOMAIN_PACKS.md](../platform/DOMAIN_PACKS.md)
- Open-core boundary: [OPEN_CORE.md](../OPEN_CORE.md)
- Series: [docs/blog/series/](../blog/series/README.md) (history → features → battery → platform morph)
- Release notes: [RELEASE_NOTES_v3.0.1.md](RELEASE_NOTES_v3.0.1.md) · [3.0.0](../RELEASE_NOTES_v3.0.0.md)
