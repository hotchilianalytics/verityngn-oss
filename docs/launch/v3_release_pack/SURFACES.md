# Additional release surfaces — VerityNgn OSS 3.0.1

Paste-ready blurbs for channels outside the Reddit pack and HN/X/LinkedIn drafts.  
**Same claims everywhere.** One primary link per post. Risk language, not lie-detector language.

| Lock | Value |
|------|-------|
| Package | **`verityngn==3.0.1`** on PyPI |
| Engine tip | `1b2cca8` · Docs/release tip `12be77d` (tag `v3.0.1`) |
| Launch | **Monday, Nov 23, 2026** |
| Gallery | https://verityindex.com/gallery |
| PyPI | https://pypi.org/project/verityngn/3.0.1/ |
| Install | `pip install 'verityngn[deep]==3.0.1'` |
| Repo | https://github.com/hotchilianalytics/verityngn-oss |
| Multimodal brief | [`MULTIMODAL_AND_FUTURES_v3.md`](MULTIMODAL_AND_FUTURES_v3.md) |
| Attach | One figure from [`FIGURES.md`](FIGURES.md) |

Do **not** advertise `pip install …==3.0.0` (`3.0.0` is yanked).  
**Pitch lock:** 45% of SB1507 claims + Lipozem doctor cards are pixel-only; 1–6 fps + brand-safety/exhibit JSONs live in 3.0.1; 3.1/3.2 = object/action semantics, visual–spoken contradiction, pose/lip/audio congruence.  
Creator / journalist **cold email stays frozen**. These are public posts only.

---

## Stagger calendar (suggested) — lock Monday Nov 23, 2026

| Day | Channel | Asset |
|-----|---------|-------|
| **Mon Nov 23** | Blog / Substack or site mirror of [`BLOG_POST.md`](BLOG_POST.md) | Full article |
| **+6–12h** | r/MachineLearning `[P]` | Pack [`README.md`](README.md) §A |
| **+12–24h** | r/LanguageTechnology | Pack README §B |
| **+24h** | **Show HN** | [`HN_POST.md`](HN_POST.md) |
| Same window | X thread · LinkedIn · **Bluesky** | Thread / post drafts |
| **+48h** | r/opensource · r/OSINT | Pack README §C–D |
| **+48–72h** | Lobsters · Changelog / TLDR / console.dev | § below |
| Optional | r/LocalLLaMA | Only with Vertex honesty |
| Optional | Streamlit wake | https://verityngn.streamlit.app — secondary CTA only |

Do **not** blast HN + Reddit + X in the same hour.

---

## Bluesky

**Single post** (attach `papers/figures/platform_layers.png`):

```
VerityNgn OSS 3.0.1 is on PyPI (launch Mon Nov 23) — Apache-2.0 multimodal claim-risk. 45% of SB1507 claims + Lipozem’s doctor cards exist only in pixels; adaptive 1–6 fps + brand-safety/exhibit JSONs live default-on. Next: 3.1 object/action semantics, 3.2 pose/lip/audio congruence. Not a lie detector.

pip install 'verityngn[deep]==3.0.1'

Proof gallery: https://verityindex.com/gallery
https://pypi.org/project/verityngn/3.0.1/
```

---

## Lobsters

**Title:** `VerityNgn 3.0.1 – OSS multimodal video claim-risk engine`

**URL:** https://pypi.org/project/verityngn/3.0.1/  
**Tags:** `ai`, `show`, `python` (adjust to site norms)

**Comment (first):**

```
CLI takes a YouTube URL or local mp4 and emits a claim-level risk report (CRAAP or SIFT packs) with an optional grounded Deep Research pass. Engine is Apache-2.0; hosted gallery/credits are on verityindex.com.

Install: pip install 'verityngn[deep]==3.0.1'. Gemini/Vertex required for the LLM path today.

Gallery proof: https://verityindex.com/gallery
Repo: https://github.com/hotchilianalytics/verityngn-oss
```

Tone: technical, no “revolutionary,” invite hard negatives.

---

## Changelog / TLDR AI / console.dev

**3–5 line blurb** (link = PyPI or gallery):

```
VerityNgn 3.0.1 — open-source multimodal engine that turns YouTube or local video into claim-level risk reports with counter-intelligence and optional Deep Research. Apache-2.0 CLI on PyPI; hosted control plane at verityindex.com. pip install 'verityngn[deep]==3.0.1'. Gallery: https://verityindex.com/gallery
```

**Shorter (TLDR-style):**

```
OSS video claim-risk CLI (multimodal + counter-intel + Deep Research). 3.0.1 on PyPI · gallery https://verityindex.com/gallery · https://pypi.org/project/verityngn/3.0.1/
```

---

## dev.to / Substack mirror

Do **not** rewrite [`docs/blog/series/`](../../blog/series/README.md). Publish [`BLOG_POST.md`](BLOG_POST.md) once, then:

```
Full write-up: [title from BLOG_POST]
Series (history → platform morph): https://github.com/hotchilianalytics/verityngn-oss/tree/release/v3.0.0/docs/blog/series
Install: pip install 'verityngn[deep]==3.0.1'
Gallery: https://verityindex.com/gallery
```

---

## Optional: r/LocalLLaMA

Only if honest about cloud LLM:

### Title
```
[Release] VerityNgn 3.0 — OSS video claim-risk pipeline (uses Gemini/Vertex today)
```

### Body
```
Not a local weights project. The open piece is the claim extract → counter-intel → report graph (Apache-2.0). Inference today is Gemini/Vertex (`VERTEX_LOCATION=global`).

pip install 'verityngn[deep]==3.0.1'
verityngn analyze <url> --deep

Gallery: https://verityindex.com/gallery
```

Skip this sub if the honesty line will get drowned by “why not local model” pile-ons you cannot staff.

---

## Engagement one-liners (any surface)

**“Is this just ChatGPT on a transcript?”**  
Multimodal frames/OCR + separate verification graph with CI weighting. DR is optional and grounded on the claim binder.

**“pip install failed.”**  
Use `pip install 'verityngn[deep]==3.0.1'` (Python ≥3.12). Do not pin `3.0.0` (yanked).

**“Where’s the demo?”**  
https://verityindex.com/gallery — not Streamlit as the primary CTA.
