# I Built an AI That Fact-Checks YouTube Videos — Here's What I Learned About Fighting Misinformation

*Video misinformation is growing faster than fact-checkers can keep up. So I built an open-source system that fights back — with counter-intelligence.*

---

## The Problem No One Is Solving

Every minute, 500 hours of video are uploaded to YouTube. That's 720,000 hours per day.

Meanwhile, professional fact-checkers can review maybe 10-20 claims per day — if they're working full-time.

The math doesn't work.

But here's what really bothers me: **existing automated fact-checking tools only analyze text**. They read the transcript and call it a day. They miss the on-screen graphics claiming "clinically proven." They miss the visual demonstrations that look convincing but are meaningless. They miss the carefully edited "testimonials" designed to deceive.

Video misinformation is fundamentally different from text misinformation. It combines multiple modalities — spoken words, visuals, on-screen text, audio cues — into a persuasive package that bypasses our critical thinking.

And there's another problem: **search engines are broken for fact-checking**.

When you Google claims from a scam supplement video, you often find... promotional press releases. Pages designed to look like news but written by the company's PR firm. The search results *confirm* the false claims because the misinformation ecosystem is optimized for SEO.

This is the adversarial reality of modern misinformation.

---

## Building VerityNgn: A Counter-Intelligence Approach

I spent the last year building **VerityNgn** (Verity Engine) — an open-source system that takes a fundamentally different approach to video verification.

The core insight: **we need counter-intelligence, not just fact-checking**.

### What Makes VerityNgn Different

**1. Multimodal Analysis — Not Just Text**

VerityNgn uses Google's Gemini 2.5 Flash to analyze the *full video* at 1 frame per second:
- Spoken words (transcript)
- On-screen text (OCR)
- Visual demonstrations
- Audio cues
- Motion and gestures

The 1M token context window means we can process up to 47 minutes of video in a single pass — no fragmented analysis that loses context.

**2. Counter-Intelligence — Actively Seeking Contradictory Evidence**

This is the key innovation. Instead of just searching for evidence that confirms or denies claims, VerityNgn actively hunts for:

- **YouTube review videos**: Independent creators who have reviewed, tested, or debunked the content
- **Press release detection**: Identifies promotional content masquerading as news (94% precision)
- **Contradiction weighting**: Evidence that contradicts the claim is weighted more heavily than confirming evidence

Why? Because misinformation is designed to generate supporting evidence. The whole SEO ecosystem is optimized to confirm false claims. Counter-intelligence cuts through this by explicitly searching for opposition.

**3. Probabilistic Truthfulness — Not Binary Verdicts**

Real-world claims are rarely simply "true" or "false." VerityNgn generates a three-state probability distribution:

- **TRUE**: Evidence supports the claim
- **FALSE**: Evidence contradicts the claim  
- **UNCERTAIN**: Insufficient or conflicting evidence

This honest uncertainty is crucial. A claim like "Product X helps with weight loss" might be TRUE for some people in some circumstances, FALSE as a general claim, and UNCERTAIN given the specific evidence available.

We report calibrated probabilities, not confident-sounding guesses.

---

## How It Works

Here's the pipeline:

```
YouTube URL 
  → Intelligent Segmentation (optimizes for 1M token context)
  → Video Download (yt-dlp)
  → Multimodal Analysis (Gemini 2.5 Flash @ 1 FPS)
  → Enhanced Claim Extraction (specificity scoring, type classification)
  → Evidence Verification (web search, scientific databases)
  → Counter-Intelligence (YouTube reviews, press release detection)
  → Probability Calculation (Bayesian aggregation)
  → Report Generation (HTML, Markdown, JSON)
```

The output is an interactive HTML report showing:
- Each claim extracted from the video
- Evidence found for and against
- Counter-intelligence findings
- Probability distribution with confidence
- Source links for verification

---

## The Results

We evaluated VerityNgn on claims spanning health supplements, financial advice, cryptocurrency, and misinformation videos:

| Metric | Result |
|--------|--------|
| **Accuracy vs. ground truth** | 75% (95% CI: 61-85%) |
| **Improvement from counter-intel** | +18% on misleading content |
| **Calibration (Brier score)** | 0.12 |
| **Precision (FALSE claims)** | 85% |

The counter-intelligence system adds 18 percentage points of accuracy on misleading content (scam videos, conspiracy theories). That's the difference between a usable system and a toy.

**Cost per video**: $0.50–$2.00 (Gemini + Search APIs)

**Processing time**: 3-5 minutes for typical videos

---

## Try It Right Now

The easiest way to try VerityNgn is the live Streamlit app:

**[verityngn.streamlit.app](https://verityngn.streamlit.app)**

1. Paste a YouTube URL
2. Click "Start Verification"
3. Browse the Gallery to see your report

No installation required. The app connects to a Cloud Run backend that does the heavy lifting.

---

## Open Source: Apache 2.0

The entire codebase is open source under Apache 2.0:

**[github.com/hotchilianalytics/verityngn-oss](https://github.com/hotchilianalytics/verityngn-oss)**

This includes:
- Complete verification engine
- Streamlit UI
- Three methodology papers with full transparency
- Docker deployment configurations
- API documentation

I'm releasing this because I believe misinformation is too important a problem to solve behind closed doors. The methodology needs to be transparent. The code needs to be auditable. The community needs to be able to improve it.

---

## Limitations (Honest Assessment)

VerityNgn is a research project, not a production fact-checking service. Here's what it can't do:

- **English only** (for now)
- **YouTube only** (no TikTok, Instagram, etc.)
- **89% stance detection accuracy** (not perfect)
- **Susceptible to coordinated campaigns** (if enough fake "review" videos exist)
- **No human in the loop** (automated system with all the limitations that implies)
- **Requires API costs** (~$0.50-2.00 per video)

The 75% accuracy means 25% of claims are incorrectly assessed. This is a tool to augment human judgment, not replace it.

---

## What's Next

Current priorities:
1. **Multi-language support** (Spanish, French, German first)
2. **Additional platforms** (TikTok, Instagram Reels)
3. **Expanded evidence sources** (Reddit, forums, specialized databases)
4. **50-video validation set** with expert-labeled ground truth

We're also exploring a commercial tier for teams that need high-volume processing — newsrooms, compliance teams, researchers.

---

## Try It, Break It, Improve It

If you're interested in misinformation research, AI, or just want to see how this works:

1. **Try the live demo**: [verityngn.streamlit.app](https://verityngn.streamlit.app)
2. **Star the repo**: [github.com/hotchilianalytics/verityngn-oss](https://github.com/hotchilianalytics/verityngn-oss)
3. **Read the methodology**: Check the `papers/` directory for full transparency
4. **Open an issue**: Found a bug? Have an idea? Let's talk.

The fight against misinformation needs all of us.

---

*Alan Coppola is the creator of VerityNgn and founder of HotChili Analytics. Follow him on X [@AlanJCoppola](https://twitter.com/AlanJCoppola) and [LinkedIn](https://linkedin.com/in/ajjcoppola).*

---

**Links:**
- Live Demo: [verityngn.streamlit.app](https://verityngn.streamlit.app)
- GitHub: [github.com/hotchilianalytics/verityngn-oss](https://github.com/hotchilianalytics/verityngn-oss)
- Research Paper: [papers/verityngn_research_paper.md](https://github.com/hotchilianalytics/verityngn-oss/blob/main/papers/verityngn_research_paper.md)


