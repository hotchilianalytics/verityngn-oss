# VerityNgn Testing Guide

Comprehensive guide to testing VerityNgn functionality.

---

## Quick Test

### Test Credentials

```bash
python test_credentials.py
```

Expected output:

```
✅ Google Cloud Project: your-project-id
✅ Vertex AI Authentication: SUCCESS
✅ Service Account: service-account@project.iam.gserviceaccount.com
✅ Location: us-central1
✅ All required credentials configured!
```

### Test Workflow

```bash
./run_test_tl.sh
```

This tests the complete workflow on the LIPOZEM video (tLJC8hkK-ao, 33 minutes).

**Expected:**
- Duration: ~10 minutes
- Claims extracted: 15-25
- Report generated in `outputs/tLJC8hkK-ao/`

---

## Test Scripts

### 1. Credential Validation

**File:** `test_credentials.py`

**Purpose:** Verify authentication setup

**Usage:**

```bash
python test_credentials.py
```

**Tests:**
- Service account or ADC authentication
- Vertex AI access
- Project ID configuration
- Location configuration

### 2. Enhanced Claims Extraction

**File:** `test_enhanced_claims.py`

**Purpose:** Test multi-pass claims extraction with specificity scoring

**Usage:**

```bash
python test_enhanced_claims.py
```

**Tests:**
- Initial claim extraction
- Specificity scoring
- Absence claim generation
- Quality filtering

### 3. Segmented Analysis

**File:** `debug_segmented_analysis.py`

**Purpose:** Test intelligent video segmentation

**Usage:**

```bash
python debug_segmented_analysis.py
```

**Tests:**
- Segmentation calculation
- YouTube URL analysis
- Progress logging
- Context window utilization

### 4. Full Workflow

**File:** `test_tl_video.py`

**Purpose:** Complete end-to-end verification workflow

**Usage:**

```bash
python test_tl_video.py
```

**Tests:**
- Video metadata extraction
- Multimodal analysis
- Claims extraction
- Evidence verification
- Counter-intelligence
- Report generation

---

## Test Videos

### LIPOZEM Video (tLJC8hkK-ao)

**URL:** https://www.youtube.com/watch?v=tLJC8hkK-ao

**Properties:**
- Duration: 33 minutes
- Type: Health supplement marketing
- Complexity: High (many claims)

**Expected Results:**
- Segments: 1
- Processing time: 8-12 minutes
- Claims: 15-25
- Counter-intel: Multiple YouTube reviews found
- Press releases: Detected

**Good for testing:**
- Intelligent segmentation (33min fits in 1 segment)
- Health claim verification
- Counter-intelligence system
- Press release detection

### Rick Roll (dQw4w9WgXcQ)

**URL:** https://www.youtube.com/watch?v=dQw4w9WgXcQ

**Properties:**
- Duration: 3.5 minutes
- Type: Music video
- Complexity: Low (no factual claims)

**Expected Results:**
- Segments: 1
- Processing time: 5-8 minutes
- Claims: 0-2 (mostly descriptive)

**Good for testing:**
- Short video processing
- Handling content with no claims
- Basic functionality

---

## Debugging Tools

### VS Code Debugger

**Configuration:** `.vscode/launch.json`

**Available Configurations:**

1. **"Debug: Test TL Video"**
   - Runs full workflow with debugger attached
   - Environment variables loaded from `.env`
   - Breakpoints enabled

2. **"Debug: Segmented Analysis Test"**
   - Tests segmentation in isolation
   - Good for debugging hanging issues

**Usage:**

1. Open `test_tl_video.py` or `debug_segmented_analysis.py`
2. Set breakpoints
3. Press F5 or use Debug menu
4. Select configuration

### Progress Logging

All workflows include detailed progress logging:

```
🎬 [VERTEX] Segmentation plan: 1998s video → 1 segment(s) of 2860s each
   Expected time: ~8-12 minutes total

🎬 [VERTEX] Segment 1/1: Processing 0s → 1998s (33.3 minutes)
   ⏱️  Expected processing time: 8-12 minutes for this segment
   📊 Progress: 0% complete
   ⏳ Please wait... (this is NORMAL, not hung)
```

### Environment Check

**File:** `check_env_complete.sh`

**Usage:**

```bash
./check_env_complete.sh
```

**Checks:**
- `.env` file exists
- Required variables set
- Service account file exists
- Google Cloud authentication

---

## Test Scenarios

### Scenario 1: First-Time Setup

**Goal:** Verify fresh installation works

**Steps:**

```bash
# 1. Clone repo
git clone https://github.com/hotchilianalytics/verityngn-oss.git
cd verityngn-oss

# 2. Install dependencies
conda env create -f environment.yml
conda activate verityngn

# 3. Setup credentials (see SETUP.md)
# ... create service-account.json and .env ...

# 4. Test credentials
python test_credentials.py

# 5. Run quick test
./run_test_tl.sh
```

**Expected:** All tests pass, report generated in ~10 minutes

### Scenario 2: Segmentation Verification

**Goal:** Confirm intelligent segmentation works correctly

**Steps:**

```bash
# 1. Run segmentation test
python debug_segmented_analysis.py

# 2. Check logs for:
#    - Optimal segment calculation
#    - Context utilization percentage
#    - Expected processing time

# 3. Verify segment count matches expectation:
#    - 10min video → 1 segment
#    - 33min video → 1 segment
#    - 60min video → 2 segments
```

**Expected:** Segments calculated optimally, 40-60% context usage

### Scenario 3: Enhanced Claims Quality

**Goal:** Verify multi-pass extraction produces quality claims

**Steps:**

```bash
# 1. Run enhanced claims test
python test_enhanced_claims.py

# 2. Check output for:
#    - Initial claims count
#    - Specificity scores (should be 60-100 for kept claims)
#    - Absence claims generated
#    - Vague claims filtered out

# 3. Verify claims have:
#    - Numbers/percentages (specificity)
#    - Specific entities
#    - Minimal hedging language
```

**Expected:** High-quality, verifiable claims with specificity scores

### Scenario 4: Counter-Intelligence

**Goal:** Verify counter-intel system finds reviews and press releases

**Steps:**

```bash
# 1. Run full workflow on health supplement video
python test_tl_video.py

# 2. Check report for:
#    - YouTube reviews section
#    - Press release detection
#    - Credibility weighting

# 3. Verify counter-intel impact:
#    - Reviews found: 2-5+
#    - Press releases detected: Yes/No
#    - Impact on final probability: -0.20 per review
```

**Expected:** Counter-intel findings integrated into report

### Scenario 5: Performance Benchmarking

**Goal:** Measure v2.0 performance improvements

**Steps:**

```bash
# 1. Record start time
date

# 2. Run 33-minute video
python test_tl_video.py

# 3. Record end time
date

# 4. Calculate duration and compare:
#    - v1.0: 56-84 minutes (7 segments)
#    - v2.0: 8-12 minutes (1 segment)
```

**Expected:** ~10 minutes for 33-minute video (6-7x speedup)

---

## Automated Testing

### Unit Tests

```bash
# Run all unit tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_segmentation.py

# Run with verbose output
python -m pytest -v tests/
```

### Integration Tests

```bash
# Test complete workflow
python test_tl_video.py

# Test with timeout protection
python test_tl_video_debug.py
```

### Batch Testing

```bash
# Test multiple videos
python test_videos_batch.py
```

---

## Common Test Failures

### "Empty response from segmented Vertex YouTube analysis"

**Cause:** Segment too large, network timeout, or API error

**Solution:**

1. Check video duration vs segment size
2. Override segment duration:
   ```bash
   # In .env
   SEGMENT_DURATION_SECONDS=1800  # 30 minutes
   ```
3. Check Google Cloud quotas
4. Verify network connection

### "ModuleNotFoundError"

**Cause:** Missing dependencies

**Solution:**

```bash
pip install -r requirements.txt --force-reinstall
```

### "Could not determine credentials"

**Cause:** Authentication not configured

**Solution:**

1. Check `test_credentials.py` output
2. Verify `.env` has `GOOGLE_CLOUD_PROJECT`
3. Verify service account JSON exists
4. See [SETUP.md](SETUP.md)

### "Permission denied for Vertex AI"

**Cause:** Service account lacks permissions

**Solution:**

```bash
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
    --member="serviceAccount:SERVICE-ACCOUNT-EMAIL" \
    --role="roles/aiplatform.user"
```

---

## Test Output Validation

### Expected Report Structure

```
outputs/VIDEO_ID/
├── report.html          # Main report (must exist)
├── report.md            # Markdown (must exist)
├── report.json          # JSON (must exist)
└── VIDEO_ID_claim_N_sources.html  # Per-claim evidence (N claims)
```

### Report Quality Checklist

- ✅ Claims section populated (10-30 claims typical)
- ✅ Each claim has specificity score
- ✅ Evidence sources listed (30-100+ sources)
- ✅ Probability distribution present (TRUE/FALSE/UNCERTAIN)
- ✅ Counter-intelligence findings (if applicable)
- ✅ Press release detection results
- ✅ Validation power scores for sources

### Segmentation Validation

Check logs for:

```
✅ Optimal segment duration calculated
✅ Context utilization: 40-60%
✅ Processing time matches expectation (8-12 min per segment)
✅ All segments processed successfully
```

---

## Performance Metrics

### Expected Performance (v2.0)

| Video Duration | Segments | API Calls | Time | Context Usage |
|----------------|----------|-----------|------|---------------|
| 10 min | 1 | 1 | 8-12 min | 21% |
| 20 min | 1 | 1 | 8-12 min | 42% |
| 33 min | 1 | 1 | 8-12 min | 58% |
| 60 min | 2 | 2 | 16-24 min | 53% |
| 120 min | 3 | 3 | 24-36 min | 70% |

### Comparison to v1.0

| Metric | v1.0 | v2.0 | Improvement |
|--------|------|------|-------------|
| API Calls (33min) | 7 | 1 | 86% reduction |
| Processing Time | 56-84 min | 8-12 min | 6-7x faster |
| Context Usage | 3% | 58% | 19x better |

---

## Continuous Testing

### Pre-Commit Testing

Before committing changes:

```bash
# 1. Run credential test
python test_credentials.py

# 2. Run segmentation test
python debug_segmented_analysis.py

# 3. Run quick workflow test
./run_test_tl.sh
```

### Pre-Release Testing

Before releasing:

```bash
# 1. Test with multiple videos
python test_videos_batch.py

# 2. Performance benchmarking
python test_performance.py

# 3. Integration tests
python -m pytest tests/

# 4. Manual verification
#    - Check report quality
#    - Verify counter-intel works
#    - Check all output formats (HTML, MD, JSON)
```

---

## Next Steps

- **[Setup Guide](SETUP.md)** - Configure authentication
- **[Quick Start](QUICK_START.md)** - Run your first verification
- **[Troubleshooting](../TROUBLESHOOTING.md)** - Common issues
- **[Architecture](../ARCHITECTURE.md)** - Technical details

---

**Last Updated:** October 28, 2025  
**Version:** 2.0








