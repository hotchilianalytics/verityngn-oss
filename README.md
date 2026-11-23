# VerityNgn

**Claim-level risk abatement for video**

[![Documentation](https://img.shields.io/badge/docs-mintlify-blue.svg)](https://hotchilianalyticsllc.mintlify.app)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Research](https://img.shields.io/badge/status-research-yellow.svg)]()

> **Current OSS runtime:** `verityngn==3.0.1` on PyPI (`release/v3.0.0` branch; `3.0.0` yanked).
> Launch lock: **Monday, Nov 23, 2026** · docs tip `12be77d` (tag `v3.0.1`). Analysis / verification / Deep Research default to
> `gemini-3.8-flash`, always emit `report.html` + `deep.html`, and share a Vertex fallback
> policy across `global` and `us-central1`.

---

## Quick start (v3.0.1)

```bash
pip install 'verityngn[deep]==3.0.1'
# Optional sleeves already in the wheel:
#   pip install 'verityngn[vision,audio,predictions]==3.0.1'
# Public Lipozem demo
verityngn analyze --tier full --deep 'https://www.youtube.com/watch?v=tLJC8hkK-ao'
# Analyst local file (SB1507 — provide your own path to the mp4)
verityngn analyze --tier local-full --deep -f /path/to/sb1507.mp4 -o outputs/release_v3_sb1507_dense
# CEO talking-head
verityngn analyze --tier full --deep 'https://www.youtube.com/watch?v=lb_ZJylekWo'
```

Copy-paste fixtures, scorecard counts, and what is *not* in the wheel: [`docs/launch/EXAMPLES.md`](docs/launch/EXAMPLES.md).  
Multimodal pitch + 3.1/3.2 futures brief: [`docs/launch/v3_release_pack/MULTIMODAL_AND_FUTURES_v3.md`](docs/launch/v3_release_pack/MULTIMODAL_AND_FUTURES_v3.md).

Open-core boundary: [`docs/OPEN_CORE.md`](docs/OPEN_CORE.md) · Dependency model: [`docs/DEPENDENCY_MODEL.md`](docs/DEPENDENCY_MODEL.md) · Promotion checklist: [`docs/launch/OSS_BATCH_COMMERCIAL_PROMOTION.md`](docs/launch/OSS_BATCH_COMMERCIAL_PROMOTION.md) · Gemini gap: [`docs/research/GEMINI_2026_CAPABILITY_GAP.md`](docs/research/GEMINI_2026_CAPABILITY_GAP.md)

---

## What's in v3.0.1 (Multimodal Risk Today)

Default-on in every full run (no extra extras required):

- **Adaptive 1–6 fps content-aware sampling** — `lecture_vsl` @ 1 fps → `montage_motion` @ 3 → HIGH `exhibit_slide` @ 4 (depositions/earnings) → HIGH `flash_ocr` @ 6 (ads/Shorts); `--tier auto` escalates slide-heavy videos via optical `visual_text_density`.
- **Pixel-sourced claims** — four modalities (`visual_text`, `graphic`, `chart`, `demonstration`). 10 v3 release runs: **81** verified pixel-only claims (69 within the final primary-10); **18/40 (45%)** on SB1507 legislative charts/tables; silent testimonial/credential cards on Lipozem; exhibit OCR on Butler Kahn; CES/CNBC boards.
- **Visual risk sidecars** — `brand_safety_scores.json` (`visual_only_high_risk_count`, credential-flash, sub-1000ms disclosure blink risk) and `{video_id}_exhibit_map.json` (Bates/OCR ledger). Deep Research (`--deep`) leads with a `visual_only_claims` array.
- **Six claim kinds**, CRAAP/SIFT domain packs, counter-intel, calibrated Supported / Contested / Unresolved.

**Opt-in sleeves already shipped in the 3.0.1 wheel** (not default-on): `verityngn[vision]` (MediaPipe 478 landmarks / 52 blendshapes / HFAsy_proxy), `verityngn[audio]` (prosody / VAD / TTS cues), `verityngn[predictions]` + `MULTISENSE_ENABLED=1` (S00–S15, Tier A/B), `VN_AGENTIC_VIDEO=1`, fail-closed AuthenticityGate.

## Roadmap (v3.1 / v3.2): Multimodal Semantics & Cross-Modal Congruence

| Release | Turning default-on |
|---------|-------------------|
| **3.1** | Object / prop / action semantics; visual–spoken contradiction; temporal splice risk (today’s prompts catch slides/OCR more than physical demos — 4/81 demonstrations across the 10 v3 release runs) |
| **3.2** | Pose / lip / face / audio congruence atop in-repo MediaPipe + MultiSense sleeves — framed as **delivery / conviction / disclosure risk**, never lie detection |

Heritage threads merging into that roadmap: Spot Runner emotional-arc indexing, Speech Craft / Mayew vocal Q&A reactivity, Banker HFAsy, Krykoniuk derailment, Kim/Muhn disclosure → ClearFactor, plus negative-result hygiene (refuse near-chance S14; no synthetic vision fills).

---

## What is VerityNgn?

VerityNgn is an open-source engine that analyzes YouTube or local video to produce **claim-level risk assessments** (disclosure risk, delivery risk, brand-safety / sponsor-readiness):

- Multimodal analysis: video, audio, OCR, motion, and transcript
- Evidence verification with web search and source reputation tiers
- Counter-intelligence: YouTube reviews and press-release bias detection
- Internal calibrated TRUE/FALSE/UNCERTAIN probabilities (display as Supported / Contested / Unresolved)
- Reports: JSON-first standard report + Deep Research brief with stable aliases
  `report.html` and `deep.html`

### How It Works

```
YouTube URL or mp4 -> JSON-first analysis -> claim extraction -> verification + counter-intel -> `report.html` + `deep.html`
```

1. **Tiered routing**: `auto` selects transcript-first vs full multimodal based on caption and visual sufficiency.
2. **Modality control**: `--modality auto|transcript|video` lets operators force the extraction path.
3. **Fallback-aware LLM routing**: Vertex `global` -> lower Vertex models -> `us-central1` -> Developer API.
4. **Source finding**: verification now keeps light-search sources for previously skipped promotional claims and falls back to evidence-derived URLs when needed.
5. **Dual outputs**: standard + Deep Research artifacts are synchronized into the requested output directory.

---

## 🚀 Quick Start

### Zero-friction CLI (2026-07 unfreeze)

```bash
git clone https://github.com/hotchilianalytics/verityngn-oss.git
cd verityngn-oss
pip install 'verityngn[deep]==3.0.1'
# Or from a clone: pip install -e '.[deep]'

# Set Vertex / search keys in .env (see .env.example)
verityngn analyze --tier full --deep "https://www.youtube.com/watch?v=tLJC8hkK-ao"

# Local file (depositions, court video) — no YouTube required
verityngn analyze --file /path/to/clip.mp4 --title "Expert witness excerpt"
```

Output: `{video_id}_report.md` in `.outputs/{video_id}/`.

---

VerityNgn also supports three deployment options:

### Option 1: Local-First Deployment (Recommended)

**VerityNgn is now local-first by default.** Run everything on your machine with optional cloud enhancements.

```bash
# Clone repository
git clone https://github.com/hotchilianalytics/verityngn-oss.git
cd verityngn-oss

# Configure environment
cp config.yaml.example config.yaml
# Edit config.yaml with your API keys (Search, Vertex AI)

# Run with Streamlit
streamlit run ui/streamlit_app.py
```

**Access**:
- Streamlit UI: http://localhost:8501
- API Backend: http://localhost:8080

See [docs/DEPLOYMENT_LOCAL.md](docs/DEPLOYMENT_LOCAL.md) for details.

### Option 2: Cloud Deployment (Recommended for Production)

Deploy API to Google Cloud Run + Streamlit to Streamlit Cloud:

```bash
# Deploy API
gcloud run deploy verityngn-api \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/verityngn/api:latest \
  --platform=managed \
  --region=us-central1
```

See [docs/DEPLOYMENT_CLOUD_RUN.md](docs/DEPLOYMENT_CLOUD_RUN.md) for details.

### Option 3: Google Colab (Easiest for Trying Out)

Open the Colab notebook and connect to any API endpoint:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hotchilianalytics/verityngn-oss/blob/main/notebooks/VerityNgn_Colab_Demo.ipynb)

See [docs/DEPLOYMENT_COLAB.md](docs/DEPLOYMENT_COLAB.md) for details.

---

## Heritage (v2 → v3)

Earlier releases established multimodal segmentation, claim extraction, and counter-intelligence.
**v3.0.1** is the current public surface — see [What's in v3.0.1](#whats-in-v301-multimodal-risk-today) above.
Do not pin yanked `verityngn==3.0.0`.

## Key Features

### 🎯 Multimodal Video Analysis
- Analyzes visual content, audio, on-screen text (OCR), and motion
- Uses Google Gemini multimodal models (large context window)
- **Intelligent segmentation**: Context-aware segment calculation (up to 47.7 minutes per segment)
- Processes videos up to 2+ hours with optimized segment-based analysis
- 290 tokens/second consumption rate with automatic overhead management

### 🔬 Evidence-Based Verification
- Web search with credibility weighting
- Counter-intelligence web search with source-reputation weighting (peer-reviewed and government domains ranked higher)
- Source validation power scoring (peer-reviewed = 1.5, press release = -1.0)

### 🕵️ Counter-Intelligence System
- **YouTube Review Analysis**: Searches for contradictory reviews/debunking videos
  - 76% detection rate, 89% stance accuracy
  - Credibility weighting based on views, channel, engagement
- **Press Release Detection**: Identifies promotional content
  - 94% precision, 87% recall
  - Penalizes self-referential promotional material

### 📊 Probabilistic Truthfulness
- Three-state distribution: TRUE / FALSE / UNCERTAIN
- Bayesian evidence aggregation with validation power
- Well-calibrated (Brier score = 0.12, ECE = 0.04)
- Transparent probability calculations

### 📄 Comprehensive Reports
- **HTML**: Interactive report with sources, evidence, and probability breakdowns
- **Markdown**: Human-readable summary
- **JSON**: Machine-readable structured data

---

## Quick Start

### Prerequisites

- Python 3.12+
- Google Cloud account with Vertex AI API enabled
- YouTube Data API v3 key (optional, for enhanced counter-intel)
- Google Custom Search API (for web evidence gathering)

### Installation

```bash
# Clone the repository
git clone https://github.com/hotchilianalytics/verityngn-oss.git
cd verityngn-oss

# Create and activate environment
conda env create -f environment.yml
conda activate verityngn

# The 'verityngn' package is automatically available in the project root
pip install -e .
```

### Configuration

```bash
# Copy configuration template
cp config.yaml.example config.yaml

# Edit config.yaml and add your credentials:
# - search.google_search_api_key
# - search.cse_id
# - gcp.project_id (if using Vertex AI)

# VerityNgn supports 'none' authentication for local-only browsing
# See docs/LOCAL_SETUP.md for detailed instructions
```

### Run Verification

**Command Line:**
```bash
python run_workflow.py https://www.youtube.com/watch?v=VIDEO_ID
```

**Streamlit UI:**
```bash
./run_streamlit.sh
# Open http://localhost:8501
```

**Output:**
```
outputs/
└── VIDEO_ID/
    ├── report.html      # Interactive report
    ├── report.md        # Markdown summary
    ├── report.json      # Structured data
    └── VIDEO_ID_claim_N_sources.html  # Evidence for each claim
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Input: YouTube URL                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          Intelligent Video Segmentation (NEW v2.0)           │
│  Context-aware calculation (1M token window, 290 tok/sec)   │
│  Optimal segments: 33min → 1 segment (86% fewer API calls)  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Video Download & Preprocessing                  │
│  (yt-dlp: video, audio, transcript, metadata)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            Multimodal LLM Analysis (Gemini 2.5)             │
│  Enhanced Claims Extraction with Specificity Scoring        │
│  (Extract claims from video, audio, OCR, motion)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
           ▼                       ▼
┌──────────────────────┐  ┌──────────────────────┐
│ Evidence Verification │  │  Counter-Intelligence│
│  - Web search         │  │  - YouTube reviews   │
│  - Scientific DBs     │  │  - Press releases    │
│  - Credible sources   │  │  - Contradiction     │
└──────────┬────────────┘  └──────────┬───────────┘
           │                          │
           └───────────┬──────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Probability Calculation                         │
│  (Bayesian aggregation, validation power weighting)         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 Report Generation                            │
│  (HTML, Markdown, JSON with sources and confidence)         │
└─────────────────────────────────────────────────────────────┘
```

> 📖 For detailed technical architecture, token economics, and segmentation formulas, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Research Papers

We provide complete transparency on our methodology:

- **[Main Research Paper](papers/verityngn_research_paper.md)**: Complete system methodology
- **[Counter-Intelligence Techniques](papers/counter_intelligence_methodology.md)**: YouTube reviews and press release detection
- **[Probability Model Foundations](papers/probability_model_foundations.md)**: Mathematical framework and Bayesian aggregation

All papers are written in "Sherlock mode" - maximum transparency with step-by-step calculations.

---

## Examples

### Example 1: Health Supplement Video

**Input:** YouTube video claiming "Product X causes 15 pounds of weight loss"

**Evidence Found:**
- 3 self-referential press releases (validation power: -1.0 each)
- 1 health blog (validation power: +0.4)
- 1 WebMD article (stance: UNCERTAIN, validation power: +0.9)
- 2 YouTube reviews (450K + 300K views, negative stance, validation power: +0.85, +0.72)
- 1 FDA warning (validation power: +1.3)

**Probability Distribution:**
- TRUE: 12%
- FALSE: 50%
- UNCERTAIN: 38%

**Verdict:** LIKELY FALSE

---

## Deployment

### Local Development (Research Mode)
```bash
export DEPLOYMENT_MODE=research
./run_streamlit.sh
```

### Docker Container
```bash
docker build -t verityngn:latest .
docker run -p 8501:8501 -v $(pwd)/.env:/app/.env verityngn:latest
```

### Google Cloud Run (Production)
```bash
# See DEPLOYMENT_GUIDE_PRODUCTION.md for complete instructions
gcloud run deploy verityngn-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Documentation

- **[SETUP_CREDENTIALS.md](SETUP_CREDENTIALS.md)**: Detailed credential setup
- **[METHODOLOGY.md](docs/METHODOLOGY.md)**: System architecture and approach
- **[CLAUDE.md](CLAUDE.md)**: Developer guide for contributors
- **[OSS_RELEASE_PLAN.md](OSS_RELEASE_PLAN.md)**: Roadmap and release plan
- **[SECURITY.md](SECURITY.md)**: Security policy and responsible disclosure

---

## Contributing

We welcome contributions! This is a soft launch to the academic and technical community.

**Current Priority Areas:**
- 50-video validation test set (ground truth labeling)
- Unit test coverage (currently ~40%, target 80%+)
- Additional evidence sources (Reddit, forums, specialized databases)
- Multi-language support (currently English only)
- Performance optimization

**How to Contribute:**
1. Check out [OSS_RELEASE_PLAN.md](OSS_RELEASE_PLAN.md) for roadmap
2. Open an issue to discuss your idea
3. Fork the repo and create a branch
4. Submit a pull request with tests

---

## Citation

If you use VerityNgn in your research, please cite:

```bibtex
@software{verityngn2025,
  title = {VerityNgn: A Multimodal Counter-Intelligence System for YouTube Video Verification},
  author = {HotChili Analytics},
  year = {2025},
  url = {https://github.com/hotchilianalytics/verityngn-oss},
  note = {Research software for automated fact-checking}
}
```

---

## Limitations & Disclaimer

⚠️ **Research Project**: VerityNgn is an experimental research system, not a production fact-checking service.

**Known Limitations:**
- English language only
- YouTube platform only (no Vimeo, TikTok, etc.)
- Requires API access (costs ~$0.50-2.00 per video)
- Imperfect stance detection (89% accuracy)
- Susceptible to coordinated misinformation campaigns
- No human expert review in the loop

**Disclaimer:** This system provides probabilistic assessments based on available evidence. It should not be the sole basis for important decisions. Always verify critical information with domain experts.

---

## Performance

**Accuracy (200-claim test set):**
- Overall: 78%
- With counter-intel: +18% vs baseline
- Calibration: Brier score = 0.12, ECE = 0.04

**Processing Time:**
- Average: 3-5 minutes per video
- Multimodal analysis: ~60-90 seconds
- Evidence gathering: ~2-3 minutes
- Counter-intelligence: ~1 minute

**Cost (per video):**
- Gemini 2.5 Flash: $0.30-0.80
- YouTube API: $0.05-0.10 (if enabled)
- Web search: $0.10-0.20
- **Total: ~$0.50-2.00**

---

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

Copyright 2025 HotChili Analytics

---

## Acknowledgments

Built with:
- **Google Gemini 2.5 Flash** - Multimodal LLM
- **yt-dlp** - Video downloading
- **LangChain/LangGraph** - Agent workflows
- **Streamlit** - UI framework
- **Google Cloud Platform** - Vertex AI, Storage

Special thanks to the open-source community and fact-checking researchers.

---

## Contact

- **Issues**: [GitHub Issues](https://github.com/hotchilianalytics/verityngn-oss/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hotchilianalytics/verityngn-oss/discussions)
- **Security**: See [SECURITY.md](SECURITY.md) for responsible disclosure

---

**Built with ❤️ for a more truthful internet.**
