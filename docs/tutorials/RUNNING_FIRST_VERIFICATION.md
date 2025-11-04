# Tutorial: Your First VerityNgn Verification

Step-by-step tutorial for complete beginners.

---

## What You'll Learn

By the end of this tutorial, you'll:

- ✅ Set up VerityNgn with Google Cloud authentication
- ✅ Run your first video verification
- ✅ Understand the output and reports
- ✅ Interpret truthfulness scores

**Time required:** 30 minutes

---

## Prerequisites

- Basic command line knowledge
- Google Cloud account (free tier works!)
- Python 3.12+ installed

---

## Step 1: Set Up Google Cloud (10 minutes)

### 1.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Enter project name: `verityngn-tutorial`
4. Click **"Create"**

### 1.2 Enable Required APIs

1. In the search bar, type "Vertex AI API"
2. Click **"Enable"**
3. Wait for activation (1-2 minutes)

### 1.3 Create Service Account

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **"Create Service Account"**
   - Name: `verityngn-service`
   - Click **"Create and Continue"**
3. Grant roles:
   - Add **"Vertex AI User"**
   - Click **"Continue"** → **"Done"**

### 1.4 Download Credentials

1. Click on your new service account
2. Go to **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Select **"JSON"**
5. Click **"Create"**
6. Save the file (it downloads automatically)

**Important:** Remember where you saved this file!

---

## Step 2: Install VerityNgn (5 minutes)

### 2.1 Clone Repository

```bash
# Open Terminal (macOS/Linux) or Git Bash (Windows)

# Navigate to where you want to install
cd ~/Documents  # Or any folder you prefer

# Clone the repository
git clone https://github.com/hotchilianalytics/verityngn-oss.git

# Enter the directory
cd verityngn-oss
```

### 2.2 Install Dependencies

**Using Conda (Recommended):**

```bash
# Create environment
conda env create -f environment.yml

# Activate environment
conda activate verityngn
```

**Using pip:**

```bash
# Install dependencies
pip install -r requirements.txt
```

---

## Step 3: Configure Credentials (5 minutes)

### 3.1 Place Service Account File

1. **Find** the JSON file you downloaded in Step 1.4
2. **Rename** it to `service-account.json`
3. **Move** it to the `verityngn-oss` directory

```bash
# Example (adjust path to where you downloaded):
mv ~/Downloads/verityngn-tutorial-*.json ./service-account.json
```

### 3.2 Create .env File

```bash
# Copy the example file
cp env.example .env

# Edit the file
nano .env  # Or use any text editor
```

**Add your project ID:**

```bash
# Replace YOUR-PROJECT-ID with your actual project ID from Step 1.1
GOOGLE_CLOUD_PROJECT=verityngn-tutorial
PROJECT_ID=verityngn-tutorial
LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
```

**Save and exit:**
- Nano: Press `Ctrl+X`, then `Y`, then `Enter`
- Other editors: Save and close normally

### 3.3 Verify Setup

```bash
python test_credentials.py
```

**Expected output:**

```
✅ Google Cloud Project: verityngn-tutorial
✅ Vertex AI Authentication: SUCCESS
✅ Service Account: verityngn-service@verityngn-tutorial.iam.gserviceaccount.com
✅ All required credentials configured!
```

**If you see errors:** Check [Troubleshooting Guide](../TROUBLESHOOTING.md)

---

## Step 4: Run Your First Verification (10 minutes)

### 4.1 Choose a Test Video

We'll use a short health supplement video:

**Video:** Rick Astley - Never Gonna Give You Up  
**URL:** `https://www.youtube.com/watch?v=dQw4w9WgXcQ`  
**Duration:** 3.5 minutes  
**Expected time:** ~8 minutes

### 4.2 Start the Analysis

```bash
python -m verityngn.workflows.main_workflow \
    --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### 4.3 Watch Progress

You'll see output like:

```
🎬 [VERTEX] Segmentation plan: 212s video → 1 segment(s) of 2860s each
   Expected time: ~8-12 minutes total

🎬 [VERTEX] Segment 1/1: Processing 0s → 212s (3.5 minutes)
   ⏱️  Expected processing time: 8-12 minutes for this segment
   📊 Progress: 0% complete
   ⏳ Please wait... (this is NORMAL, not hung)
```

**Don't worry if there's no output for several minutes** - multimodal analysis takes time!

### 4.4 Analysis Complete

After ~8 minutes, you'll see:

```
✅ Analysis complete! Processing claims...
✅ Claims extracted: 2
✅ Gathering evidence...
✅ Running counter-intelligence...
✅ Generating reports...
✅ Reports saved to: outputs/dQw4w9WgXcQ/
```

---

## Step 5: View Your Report (2 minutes)

### 5.1 Open HTML Report

```bash
# macOS
open outputs/dQw4w9WgXcQ/report.html

# Linux
xdg-open outputs/dQw4w9WgXcQ/report.html

# Windows
start outputs\dQw4w9WgXcQ\report.html
```

### 5.2 Report Structure

The report includes:

**1. Video Information:**
- Title, channel, duration, upload date
- Thumbnail and link to original video

**2. Truthfulness Score:**
```
TRUE:      20%
FALSE:     5%
UNCERTAIN: 75%
```

**3. Claims Analysis:**
- Each claim extracted from the video
- Specificity score (0-100)
- Evidence found
- Source credibility ratings

**4. Counter-Intelligence:**
- YouTube reviews found (if any)
- Press release detection
- Contradictory evidence

**5. Evidence Sources:**
- All sources used in verification
- Credibility scores
- Validation power (-1.0 to +1.5)

---

## Step 6: Understanding Results (5 minutes)

### 6.1 Truthfulness Distribution

**What it means:**

- **TRUE (20%)**: Some supporting evidence found
  - Not conclusive, but some claims are supported
  
- **FALSE (5%)**: Minimal contradictory evidence
  - Very few claims directly refuted
  
- **UNCERTAIN (75%)**: Not enough evidence
  - Most claims lack sufficient verification data
  - This is common for music videos!

**How to interpret:**

- **High TRUE%** (>60%): Claims well-supported, likely truthful
- **High FALSE%** (>40%): Claims contradicted, likely false
- **High UNCERTAIN%** (>50%): Insufficient evidence either way

### 6.2 Specificity Scores

Each claim has a specificity score (0-100):

- **80-100**: Highly specific, easily verifiable
  - Example: "Product causes 15 pounds of weight loss"
  
- **50-79**: Somewhat specific
  - Example: "Product helps with weight loss"
  
- **0-49**: Vague, hard to verify
  - Example: "Product improves health"

**Higher specificity = easier to verify**

### 6.3 Validation Power

Each source has a validation power score:

- **+1.5**: Peer-reviewed scientific paper
- **+1.0**: Academic or scientific source
- **+0.5**: Reputable news source
- **0.0**: General web source
- **-0.5**: Low-quality source
- **-1.0**: Press release or promotional content

**More positive = more credible**

### 6.4 Counter-Intelligence

Reports may include:

**YouTube Reviews:**
- Videos that review/debunk the original
- Credibility-weighted by views, engagement
- Each review applies -0.20 impact to truthfulness

**Press Release Detection:**
- Identifies promotional/marketing content
- Highly penalized (-1.0 validation power)
- Indicates bias in original video

---

## Step 7: Try a More Complex Video (Optional)

Now try a health supplement marketing video:

```bash
python -m verityngn.workflows.main_workflow \
    --url "https://www.youtube.com/watch?v=tLJC8hkK-ao"
```

**This video:**
- Duration: 33 minutes
- Processing time: ~10 minutes
- Claims: 15-25 expected
- Type: Health supplement marketing

**You'll see:**
- More claims extracted
- More evidence sources
- Counter-intelligence findings (YouTube reviews)
- Press release detection
- Higher TRUE/FALSE percentages (less UNCERTAIN)

---

## Next Steps

### Learn More

- **[Quick Start Guide](../guides/QUICK_START.md)** - Additional usage patterns
- **[Architecture](../ARCHITECTURE.md)** - How it works under the hood
- **[Testing Guide](../guides/TESTING.md)** - Run comprehensive tests

### Try Different Videos

**Good candidates for verification:**
- Health supplement marketing videos
- Product review videos with specific claims
- Educational content with factual claims

**Less suitable:**
- Opinion/commentary (subjective)
- Entertainment/music videos (no factual claims)
- Artistic content

### Configure Optional APIs

For enhanced functionality:

**Google Custom Search API** (better evidence gathering):
- See [Setup Guide - API Keys](../guides/SETUP.md#google-custom-search-api-for-evidence-gathering)

**YouTube Data API** (enhanced counter-intelligence):
- See [Setup Guide - API Keys](../guides/SETUP.md#youtube-data-api-v3-for-enhanced-counter-intelligence)

### Use Streamlit UI

```bash
./run_streamlit.sh
```

Then open http://localhost:8501 for a visual interface!

---

## Troubleshooting

### "Process seems hung"

**Normal:** 8-12 minutes of no output during processing

**Wait at least 12 minutes before assuming it's hung!**

See [Troubleshooting - Processing Issues](../TROUBLESHOOTING.md#processing-issues)

### "Could not determine credentials"

Check `.env` file:

```bash
cat .env
```

Should contain:
```
GOOGLE_CLOUD_PROJECT=verityngn-tutorial
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
```

See [Troubleshooting - Authentication](../TROUBLESHOOTING.md#authentication-issues)

### "Permission denied"

Grant Vertex AI permissions:

```bash
gcloud projects add-iam-policy-binding verityngn-tutorial \
    --member="serviceAccount:verityngn-service@verityngn-tutorial.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

---

## Congratulations! 🎉

You've successfully:

- ✅ Set up VerityNgn with Google Cloud
- ✅ Configured authentication
- ✅ Run your first video verification
- ✅ Interpreted truthfulness reports

You're now ready to verify any YouTube video!

---

**Last Updated:** October 28, 2025  
**Version:** 2.0


