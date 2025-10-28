# VerityNgn Quick Start Guide

Get up and running with VerityNgn in 5 minutes.

---

## Prerequisites

Before you begin, ensure you have:

- ✅ Python 3.12+ installed
- ✅ Google Cloud account
- ✅ Completed [Setup Guide](SETUP.md) (authentication configured)

---

## Quick Start

### 1. Verify Installation

```bash
cd /path/to/verityngn-oss
python test_credentials.py
```

Expected output:

```
✅ Google Cloud Project: your-project-id
✅ Vertex AI Authentication: SUCCESS
✅ All required credentials configured!
```

### 2. Run Your First Verification

**Using Streamlit UI (easiest):**

```bash
./run_streamlit.sh
```

Then:
1. Open http://localhost:8501 in your browser
2. Paste a YouTube URL
3. Click "Analyze Video"
4. Wait 8-12 minutes for a typical 30-minute video
5. View the interactive report!

**Using Command Line:**

```bash
python -m verityngn.workflows.main_workflow --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Using Test Script:**

```bash
# Test with a specific video
./run_test_tl.sh
```

### 3. View Results

Reports are saved to:

```
outputs/
└── VIDEO_ID/
    ├── report.html      # Interactive HTML report (open in browser)
    ├── report.md        # Markdown summary
    ├── report.json      # Machine-readable structured data
    └── VIDEO_ID_claim_N_sources.html  # Evidence for each claim
```

**Open the HTML report:**

```bash
# macOS
open outputs/VIDEO_ID/report.html

# Linux
xdg-open outputs/VIDEO_ID/report.html
```

---

## What to Expect

### Processing Time

| Video Length | Expected Time | Segments | API Calls |
|--------------|---------------|----------|-----------|
| 10 minutes | 8-12 minutes | 1 | 1 |
| 20 minutes | 8-12 minutes | 1 | 1 |
| 33 minutes | 8-12 minutes | 1 | 1 |
| 60 minutes | 16-24 minutes | 2 | 2 |

**Why so fast in v2.0?** Intelligent segmentation reduces API calls by 86%!

### Progress Logging

You'll see progress updates like:

```
🎬 [VERTEX] Segmentation plan: 1998s video → 1 segment(s) of 2860s each
   Expected time: ~8-12 minutes total

🎬 [VERTEX] Segment 1/1: Processing 0s → 1998s (33.3 minutes)
   ⏱️  Expected processing time: 8-12 minutes for this segment
   📊 Progress: 0% complete
   ⏳ Please wait... (this is NORMAL, not hung)

✅ Analysis complete! Processing claims...
```

**Don't worry if you see no output for 10+ minutes** - multimodal analysis takes time!

---

## Understanding the Report

### Truthfulness Score

Reports include a probabilistic truthfulness distribution:

```
TRUE:      45%  (Supporting evidence found)
FALSE:     30%  (Contradictory evidence found)
UNCERTAIN: 25%  (Insufficient evidence)
```

**How to interpret:**

- **High TRUE%**: Claims are well-supported by credible sources
- **High FALSE%**: Claims are contradicted by evidence
- **High UNCERTAIN%**: Not enough evidence to make determination

### Claims Analysis

Each claim shows:

- **Claim text**: What was claimed in the video
- **Specificity score**: 0-100 (higher = more verifiable)
- **Evidence**: Sources supporting or refuting the claim
- **Validation power**: Source credibility (-1.0 to +1.5)
  - Peer-reviewed: +1.5
  - Scientific source: +1.0
  - Press release: -1.0

### Counter-Intelligence

Reports include:

- **YouTube Reviews**: Debunking or contradictory videos found
- **Press Release Detection**: Identifies promotional content
- **Absence Claims**: What's NOT mentioned (e.g., "No peer-reviewed studies cited")

---

## Common Use Cases

### Health & Supplement Claims

```bash
# Analyze a health supplement video
python -m verityngn.workflows.main_workflow --url "https://www.youtube.com/watch?v=HEALTH_VIDEO_ID"
```

**VerityNgn excels at:**
- Detecting unsubstantiated health claims
- Finding scientific evidence (PubMed, studies)
- Identifying press releases and promotional content
- Discovering contradictory reviews

### Product Reviews

```bash
# Analyze a product review
python -m verityngn.workflows.main_workflow --url "https://www.youtube.com/watch?v=REVIEW_VIDEO_ID"
```

**VerityNgn checks for:**
- Counter-reviews and debunking videos
- Promotional bias detection
- Verifiable claims vs marketing speak

### Educational Content

```bash
# Verify educational claims
python -m verityngn.workflows.main_workflow --url "https://www.youtube.com/watch?v=EDU_VIDEO_ID"
```

**VerityNgn validates:**
- Scientific accuracy
- Source citations
- Expert credentials

---

## Tips for Best Results

### 1. Choose Verifiable Content

**Good:**
- Product reviews with specific claims
- Health/supplement marketing videos
- Educational content with factual claims

**Less Suitable:**
- Opinion/commentary videos
- Entertainment/fiction content
- Artistic performances

### 2. Allow Sufficient Time

- Don't interrupt during "Processing segment..." messages
- 10+ minutes of no output is NORMAL for large segments
- Check progress logs for status updates

### 3. Interpret Results Carefully

- High UNCERTAIN% doesn't mean FALSE - it means "not enough evidence"
- Check validation power of sources (peer-reviewed > general web)
- Review counter-intelligence findings for context

### 4. Use Full API Setup for Best Results

Without Google Custom Search API:
- ✅ Video analysis works
- ✅ Claims extraction works
- ⚠️ Limited evidence verification

With Google Custom Search API:
- ✅ Full evidence gathering
- ✅ Credible source validation
- ✅ Scientific database integration

See [Setup Guide - API Keys](SETUP.md#api-keys-optional-but-recommended)

---

## Troubleshooting

### "Process seems hung"

**Normal behavior:** 8-12 minutes of no output during segment processing

**How to check if it's really hung:**

1. Look for last log message: "Processing segment..."
2. Check timestamp - has it been > 15 minutes?
3. If yes, check network connection and API quotas

### "Empty response from analysis"

**Possible causes:**
1. Network timeout - retry with smaller video
2. API quota exceeded - check Google Cloud quotas
3. Model error - check logs for specific error

**Solution:** Try a shorter video first (< 10 minutes)

### "Permission denied"

**Cause:** Service account lacks Vertex AI permissions

**Solution:**

```bash
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
    --member="serviceAccount:SERVICE-ACCOUNT-EMAIL" \
    --role="roles/aiplatform.user"
```

See [Setup Guide - Troubleshooting](SETUP.md#troubleshooting)

---

## Next Steps

### Learn More

- **[Testing Guide](TESTING.md)** - Run comprehensive tests
- **[Architecture](../ARCHITECTURE.md)** - Understand how it works
- **[Configuration](../api/CONFIGURATION.md)** - Advanced settings
- **[Research Papers](../../papers/)** - Read the methodology

### Try Advanced Features

- **Custom segmentation:** Override automatic segment calculation
- **Batch processing:** Analyze multiple videos
- **API integration:** Use VerityNgn programmatically

### Contribute

- Report issues on GitHub
- Suggest improvements
- Share your use cases

---

## Example Workflow

Here's a complete example analyzing a 33-minute health supplement video:

```bash
# 1. Navigate to project
cd /Users/ajjc/proj/verityngn-oss

# 2. Activate environment
conda activate verityngn

# 3. Run analysis
python -m verityngn.workflows.main_workflow \
    --url "https://www.youtube.com/watch?v=tLJC8hkK-ao"

# 4. Wait ~10 minutes...

# 5. View report
open outputs/tLJC8hkK-ao/report.html
```

**Expected output:**
- Claims extracted: 15-25
- Processing time: 8-12 minutes
- Evidence sources: 50-100
- Counter-intel findings: 2-5 YouTube reviews

---

**Need help?** See [Setup Guide](SETUP.md) or [Troubleshooting](../TROUBLESHOOTING.md)

**Last Updated:** October 28, 2025  
**Version:** 2.0

