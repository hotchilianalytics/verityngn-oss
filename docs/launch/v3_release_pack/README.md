# VerityNgn OSS 3.0 — Release Push Pack (Reddit-first)

**Goal:** Get technical readers to star the repo, try `pip install verityngn`, and open one gallery report — without looking like spam.

**Framing:** Lead with **claim-level risk abatement** / **risk platform** (disclosure / delivery / sponsor-readiness). Avoid “truthfulness” / “lie detector” / “fact-check SaaS” language.

**Candidate SHA:** `b13bcf1` · Primary-10 **PASS** · Platform: [`docs/platform/PLATFORM_OVERVIEW.md`](../../platform/PLATFORM_OVERVIEW.md)

**Primary CTAs (pick one per post):**
1. Repo: https://github.com/hotchilianalytics/verityngn-oss  
2. Release candidate: branch `release/v3.0.0` (becomes `main` after operator testing)  
3. Gallery proof: https://verityindex.com/gallery  
4. Papers: `papers/verityngn_oss_v3_release.pdf` · `papers/verityngn_v3_ablation_archive.pdf`

**Assets to attach (images):**
- `papers/figures/gallery_thumb_collage.png`
- `papers/figures/gallery_live_claims_per_video.png`
- `papers/figures/open_core_architecture.png`
- `papers/figures/platform_layers.png` (platform morph)

---

## Why last Reddit attempt likely failed

| Failure mode | Fix this time |
|--------------|---------------|
| Sounded like a product launch / SaaS ad | Lead with **problem + method + one honest number**; put company last |
| Too many links / CTAs | **One** primary link in the post body; others in first comment |
| Big accuracy claims without caveats | Soften: “gallery evidence / prior eval” — invite scrutiny |
| Wall of architecture | Short post + image; details in comments or paper |
| Wrong sub norm | Match flair (`[P]` / `Show`) and tone per sub |
| Hit-and-run | Stay 24–48h answering “how do I run it?” and “what’s commercial?” |
| Same post everywhere | Unique titles; stagger by 1–2 days |

---

## Posting order (recommended)

1. **r/MachineLearning** `[P]` — densest technical audience  
2. **r/LanguageTechnology** — NLP / verification angle  
3. **r/opensource** — install + license angle (day later)  
4. **r/OSINT** — counter-intel / evidence angle (day later; no hype)  
5. Avoid blasting r/SideProject + r/Python + HN same hour  

---

## A. r/MachineLearning — copy/paste

### Title
```
[P] VerityNgn 3.0 — open-source multimodal video claim-risk platform + Deep Research (Apache-2.0)
```

### Body
```
I just cut VerityNgn OSS 3.0.0 — a local CLI that takes a YouTube URL (or a local mp4) and produces a claim-level **risk** report (disclosure / delivery / sponsor-readiness) with counter-intelligence and an optional grounded Deep Research pass.

**Why it exists:** transcript-only checkers miss on-screen graphics/OCR; naive web search often retrieves the subject’s own PR as “evidence.” VerityNgn extracts multimodal claims, then actively looks for contradictory review content and press-release-shaped sources.

**Platform angle:** the report is the evidence object; domain packs (CRAAP, SIFT, CEO sensors, disclosure) sit on one engine. Hosted control plane is verityindex.com — not a closed fork of the quality path.

**Try it**
```bash
pip install 'verityngn[deep]'
verityngn analyze --tier light 'https://www.youtube.com/watch?v=VIDEO_ID'
verityngn analyze --tier full 'https://www.youtube.com/watch?v=VIDEO_ID' --deep
verityngn captions 'https://www.youtube.com/watch?v=VIDEO_ID'   # operator VTT debug
```

**Repo / branch:** https://github.com/hotchilianalytics/verityngn-oss/tree/release/v3.0.0

**Public gallery of engine reports:** https://verityindex.com/gallery  

**Honest limits**
- English-first; YouTube + local file (not TikTok-native)
- LLM-assisted risk briefs — not a lie detector, not earnings prediction
- Predictions/sensors are optional OSS extras; hosted credits/SaaS are commercial

Happy to take hard negatives. If a report looks wrong, drop the video id.

Image: gallery claim-volume chart or platform_layers (attached)
```

### First comment (links + paper)
```
Paper (charts + gallery table): https://github.com/hotchilianalytics/verityngn-oss/blob/release/v3.0.0/papers/verityngn_oss_v3_release.md
Open-core boundary: https://github.com/hotchilianalytics/verityngn-oss/blob/release/v3.0.0/docs/OPEN_CORE.md
Platform layers: https://github.com/hotchilianalytics/verityngn-oss/blob/release/v3.0.0/docs/platform/PLATFORM_OVERVIEW.md
Primary-10 battery: https://github.com/hotchilianalytics/verityngn-oss/blob/release/v3.0.0/docs/launch/BATTERY_RESULTS_v3.md
Streamlit demo (optional): https://verityngn.streamlit.app
```

---

## B. r/LanguageTechnology — shorter

### Title
```
VerityNgn 3.0: multimodal claim extraction + counter-intel verification for YouTube (OSS)
```

### Body
```
Release note for an open-source pipeline that:

1. extracts verifiable claims from video (vision + transcript)
2. verifies with web/YouTube counter-evidence
3. optionally runs a grounded Deep Research forensic summary (`--deep`)

Install: `pip install 'verityngn[deep]'` then `verityngn analyze <url> --deep`

Branch: https://github.com/hotchilianalytics/verityngn-oss/tree/release/v3.0.0  
Gallery examples: https://verityindex.com/gallery

Not claiming SOTA on a shared leaderboard yet — looking for critique of the claim typology and CI weighting.
```

---

## C. r/opensource

### Title
```
Release: VerityNgn 3.0 — Apache-2.0 video claim-risk engine (CLI + Deep Research)
```

### Body
```
Open-core video claim-risk engine. v3 puts Deep Research and research sleeves (predictions sensors) in the Apache tree; hosted SaaS / credits stay on verityindex.com.

`pip install verityngn` · `verityngn analyze <url> --deep`

https://github.com/hotchilianalytics/verityngn-oss/tree/release/v3.0.0
```

---

## D. r/OSINT (careful tone)

### Title
```
Open-source tool: claim-level risk reports from YouTube videos (counter-intel search)
```

### Body
```
Sharing an OSS CLI that produces structured claim-risk reports from YouTube or local video files, with an explicit counter-intelligence step (looks for independent review videos / promotional-source patterns).

Meant as a research aid — human review still required. Not a courtroom-ready authenticity oracle.

Branch: https://github.com/hotchilianalytics/verityngn-oss/tree/release/v3.0.0  
Example gallery: https://verityindex.com/gallery
```

---

## Engagement scripts (replies)

**“Is this just ChatGPT wrapping YouTube?”**  
Claims are multimodal (frames/OCR/transcript). Verification is a separate graph with timeouts, domain tiers, and CI. Deep Research is an optional grounded pass over a sanitized report JSON.

**“What’s free vs paid?”**  
Engine quality (including Deep Research and optional predictions sensors) is OSS Apache-2.0. Hosted multi-tenant delivery / credits are commercial on verityindex.com. ClearFactor disclosure **services** (vault / counsel briefs) are paid; disclosure **engine** opens as a sleeve.

**“Show me numbers.”**  
Point to primary-10 battery (`docs/launch/BATTERY_RESULTS_v3.md`) and gallery. Don’t invent new accuracy % in comments.

**“How do I run without GCP?”**  
Gemini/Vertex credentials are required for the LLM path today; documented in `.env.example`. Local-file path skips yt-dlp.

---

## Checklist before submit

- [ ] Account has karma / isn’t brand-new empty  
- [ ] One image attached (claims-per-video, collage, or platform_layers)  
- [ ] Only one primary URL in body  
- [ ] No “revolutionary / disrupt / lie detector / alpha” language  
- [ ] First comment ready with paper + OPEN_CORE + platform overview  
- [ ] Calendar: reply window for 48h  

---

## Companion channels (after Reddit, not instead)

| Channel | Asset |
|---------|-------|
| Show HN | `docs/launch/HN_POST.md` / pack `HN_POST.md` |
| LinkedIn | `LINKEDIN_POST.md` |
| X | `X_THREAD.md` |
| Blog | `BLOG_POST.md` |
| Media checklist | `MEDIA_CHECKLIST.md` |
| Exec summary | `docs/launch/EXEC_SUMMARY_v3.md` |

Stagger ≥6–12h after the ML post so Reddit doesn’t see a synchronized blast.
