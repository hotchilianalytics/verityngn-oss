# VerityNgn

**AI-Powered YouTube Video Verification Engine**

[![Documentation](https://img.shields.io/badge/docs-mintlify-blue.svg)](https://hotchilianalyticsllc.mintlify.app)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Research](https://img.shields.io/badge/status-research-yellow.svg)]()

> **Note:** This is a research project in active development. It is currently in soft launch for the academic and technical community.

---

## What is VerityNgn?

VerityNgn (Verity Engine) is an open-source system that analyzes YouTube videos to assess the truthfulness of claims using:

- 🎥 **Multimodal Analysis**: Video, audio, OCR, motion, and transcript analysis
- 🔍 **Evidence Verification**: Web search, scientific databases, and credible sources
- 🕵️ **Counter-Intelligence**: YouTube reviews and press release detection
- 📊 **Probabilistic Assessment**: TRUE/FALSE/UNCERTAIN distributions with confidence scores
- 📄 **Comprehensive Reports**: HTML, Markdown, and JSON outputs

### How It Works

```
YouTube URL → Local/Cloud LLM Analysis → Enhanced Claims Extraction → Evidence Verification → Counter-Intel → Local-First Report
```

1. **Intelligent Segmentation**: Optimizes video segments based on 1M token context window (86% fewer API calls)
2. **Download & Analyze**: Extracts video, audio, transcript, and metadata
3. **Enhanced Claims Extraction**: Multi-pass extraction with specificity scoring and absence claim generation
4. **Gather Evidence**: Searches web, scientific sources, and press releases
5. **Counter-Intelligence**: Finds YouTube reviews and contradictory evidence
6. **Calculate Probabilities**: Bayesian aggregation with validation power weighting
7. **Generate Report**: Creates detailed HTML report with sources and confidence

---

## 🚀 Quick Start

VerityNgn supports three deployment options:

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

## What's New in v2.0

### 🚀 Intelligent Video Segmentation
- **Context-aware segmentation**: Automatically calculates optimal segment sizes based on model context window (1M tokens)
- **86% fewer API calls**: 33-minute video processed in 1 segment instead of 7
- **58% context utilization**: Maximizes use of available token budget
- **6-7x faster**: Typical 30-minute videos complete in 8-12 minutes instead of 56-84 minutes
- **Token economics**: 290 tokens/second consumption rate with smart overhead management

### 🎯 Enhanced Claims Extraction
- **Multi-pass extraction**: Initial broad extraction → specificity scoring → quality filtering → ranking
- **Absence claim generation**: Automatically identifies what's NOT mentioned (e.g., "no peer-reviewed studies cited")
- **Specificity scoring**: Rates claims from 0-100 on verifiability
- **Type classification**: Scientific, statistical, causal, comparative, testimonial, expert opinion
- **Intelligent filtering**: Removes vague claims, keeps high-quality verifiable statements

### 🔧 Improved Counter-Intelligence
- **Balanced impact model**: Refined from -0.35 to -0.20 for YouTube review influence
- **Enhanced credibility weighting**: Views, channel authority, and engagement metrics
- **Better integration**: Seamlessly works with intelligent segmentation
- **Maintained accuracy**: 94% precision on press release detection, 76% on review detection

### 📊 Performance Improvements
- **API efficiency**: 86% reduction in calls for typical videos
- **Context utilization**: 3% → 58% (19x improvement)
- **Processing speed**: 6-7x faster for 30-minute videos
- **Cost reduction**: Proportional to API call reduction

---

## Key Features

### 🎯 Multimodal Video Analysis
- Analyzes visual content, audio, on-screen text (OCR), and motion
- Uses Google Gemini 2.5 Flash (1M token context window)
- **Intelligent segmentation**: Context-aware segment calculation (up to 47.7 minutes per segment)
- Processes videos up to 2+ hours with optimized segment-based analysis
- 290 tokens/second consumption rate with automatic overhead management

### 🔬 Evidence-Based Verification
- Web search with credibility weighting
- Scientific database integration (PubMed, academic sources)
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
