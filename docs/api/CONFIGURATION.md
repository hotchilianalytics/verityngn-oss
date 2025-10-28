# VerityNgn Configuration Reference

Complete reference for all configuration options.

---

## Environment Variables

VerityNgn is configured via environment variables in a `.env` file.

### Create .env File

```bash
# Copy template
cp env.example .env

# Edit
nano .env
```

---

## Required Configuration

### Google Cloud

```bash
# Project ID (required)
GOOGLE_CLOUD_PROJECT=your-project-id
PROJECT_ID=your-project-id  # Alias

# Region (required)
LOCATION=us-central1

# Service Account (required if not using ADC)
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
```

**Notes:**
- `GOOGLE_CLOUD_PROJECT` and `PROJECT_ID` are aliases (set both for compatibility)
- `LOCATION` should be a Vertex AI supported region (us-central1 recommended)
- `GOOGLE_APPLICATION_CREDENTIALS` points to service account JSON file

---

## Optional APIs

### Google Custom Search (Evidence Gathering)

```bash
# Google API Key
GOOGLE_API_KEY=AIza...

# Custom Search Engine ID
GOOGLE_CSE_ID=your-cse-id
```

**Without these:**
- ✅ Core functionality works
- ⚠️ Limited evidence verification
- ⚠️ Fewer source citations in reports

**To set up:**
1. Create API key: https://console.cloud.google.com/apis/credentials
2. Create CSE: https://programmablesearchengine.google.com/

### YouTube Data API v3 (Counter-Intelligence)

```bash
# YouTube API Key
YOUTUBE_API_KEY=AIza...
```

**Without this:**
- ✅ Core functionality works
- ✅ Uses yt-dlp fallback (automatic)
- ⚠️ Slower metadata extraction

**To set up:**
1. Enable YouTube Data API v3
2. Create API key: https://console.cloud.google.com/apis/credentials

---

## Model Configuration

### Vertex AI Model

```bash
# Model name (default: gemini-2.5-flash)
VERTEX_MODEL_NAME=gemini-2.5-flash

# Alternative models:
# VERTEX_MODEL_NAME=gemini-1.5-pro      # Larger context (2M tokens)
# VERTEX_MODEL_NAME=gemini-1.5-flash    # Smaller output (8K tokens)
```

**Model Comparison:**

| Model | Context | Max Output | Speed | Cost | Best For |
|-------|---------|------------|-------|------|----------|
| gemini-2.5-flash | 1M | 65K | Fast | Low | Default (recommended) |
| gemini-1.5-pro | 2M | 8K | Medium | High | Very long videos |
| gemini-1.5-flash | 1M | 8K | Fastest | Lowest | Budget-conscious |

### Output Token Limits

```bash
# Max output tokens for Gemini 2.5 Flash (default: 65536)
MAX_OUTPUT_TOKENS_2_5_FLASH=65536

# Max output tokens for Gemini 1.5 models (default: 8192)
MAX_OUTPUT_TOKENS_1_5=8192
```

**Notes:**
- Higher tokens = more detailed claims extraction
- Don't exceed model limits (will error)
- 65K is optimal for 2.5 Flash

### Thinking Budget

```bash
# Thinking tokens budget (default: 0)
THINKING_BUDGET=0

# For complex reasoning (slower, more expensive):
# THINKING_BUDGET=10000
```

**Recommendations:**
- **0**: Fast mode (default) - no internal reasoning tokens
- **10000**: Deep analysis mode - model thinks before responding
- Higher = slower but potentially better quality

---

## Video Segmentation

### Intelligent Segmentation (Automatic)

```bash
# Leave commented out for automatic calculation (recommended)
#SEGMENT_DURATION_SECONDS=3000
```

**Behavior:**
- System auto-calculates optimal segment duration
- Maximizes context window utilization (40-60%)
- Minimizes API calls (86% reduction)

**For 33-minute video:**
- Calculates: 1 segment of 2860 seconds
- Context usage: 58%
- API calls: 1 (vs 7 in v1.0)

### Manual Segmentation Override

```bash
# Force specific segment duration (seconds)
SEGMENT_DURATION_SECONDS=1800  # 30 minutes
```

**Use cases:**
- Debugging: Use short segments (300-600s)
- API errors: Reduce segment size
- Special requirements: Custom durations

**Trade-offs:**
- Shorter segments: More API calls, higher cost
- Longer segments: Risk of timeout, larger memory

### Frame Rate

```bash
# Frames per second for video analysis (default: 1.0)
SEGMENT_FPS=1.0
```

**Recommendations:**
- **1.0 FPS**: Optimal balance (default) - captures all visual content
- **0.5 FPS**: Slower, cheaper - good for static content
- **2.0 FPS**: Higher detail - use only if needed (doubles token cost)

**Token impact:**
- 1 FPS: 258 tokens/sec video
- 0.5 FPS: 129 tokens/sec video
- 2 FPS: 516 tokens/sec video

---

## Claims Extraction

### Enhanced Claims Extraction

```bash
# Enable multi-pass extraction (default: true)
ENABLE_ENHANCED_CLAIMS=true

# Enable absence claim generation (default: true)
ENABLE_ABSENCE_CLAIMS=true

# Specificity threshold (0-100, default: 60)
CLAIM_SPECIFICITY_THRESHOLD=60
```

**Notes:**
- `ENABLE_ENHANCED_CLAIMS`: Multi-pass extraction with specificity scoring
- `ENABLE_ABSENCE_CLAIMS`: Generate claims about missing evidence
- `CLAIM_SPECIFICITY_THRESHOLD`: Minimum score to keep claim (higher = stricter)

### Claim Filtering

```bash
# Maximum claims to extract (default: 50)
MAX_CLAIMS=50

# Minimum claim length in characters (default: 20)
MIN_CLAIM_LENGTH=20

# Maximum claim length in characters (default: 500)
MAX_CLAIM_LENGTH=500
```

---

## Counter-Intelligence

### YouTube Review Search

```bash
# Enable YouTube counter-intelligence (default: true)
ENABLE_YOUTUBE_COUNTER_INTEL=true

# Review impact weight (default: -0.20)
YOUTUBE_REVIEW_IMPACT=-0.20

# Maximum reviews to consider (default: 10)
MAX_YOUTUBE_REVIEWS=10
```

**Notes:**
- `YOUTUBE_REVIEW_IMPACT`: How much each review affects truthfulness (-0.35 in v1.0, -0.20 in v2.0)
- Negative value = reduces truthfulness score
- Lower magnitude = less aggressive impact

### Press Release Detection

```bash
# Enable press release detection (default: true)
ENABLE_PRESS_RELEASE_DETECTION=true

# Press release validation power (default: -1.0)
PRESS_RELEASE_POWER=-1.0
```

**Notes:**
- Press releases heavily penalized (promotional bias)
- `-1.0` validation power vs `+1.5` for peer-reviewed

---

## Storage Configuration

### Deployment Mode

```bash
# Deployment mode: research | container | production
DEPLOYMENT_MODE=research
```

**Modes:**

| Mode | Storage | Best For |
|------|---------|----------|
| research | ./outputs/ | Local development |
| container | /var/tmp/ | Docker containers |
| production | GCS | Cloud Run, production |

### Storage Backend

```bash
# Storage backend: local | gcs
STORAGE_BACKEND=local

# GCS bucket name (required if STORAGE_BACKEND=gcs)
GCS_BUCKET_NAME=your-bucket-name
```

### Local Storage Paths

```bash
# Output directory (default: ./outputs)
OUTPUT_DIR=./outputs

# Downloads directory (default: ./downloads)
DOWNLOADS_DIR=./downloads

# Logs directory (default: ./logs)
LOGS_DIR=./logs
```

---

## Logging

### Log Level

```bash
# Log level: DEBUG | INFO | WARNING | ERROR (default: INFO)
LOG_LEVEL=INFO
```

**Levels:**
- **DEBUG**: Verbose output, all operations logged
- **INFO**: Normal operation, important events (default)
- **WARNING**: Only warnings and errors
- **ERROR**: Only errors

### Log Output

```bash
# Log to file (default: true)
LOG_TO_FILE=true

# Log to console (default: true)
LOG_TO_CONSOLE=true

# Log file path (default: logs/verityngn.log)
LOG_FILE=logs/verityngn.log
```

### Unbuffered Output

```bash
# For real-time progress (especially in Docker)
PYTHONUNBUFFERED=1
```

---

## Performance Tuning

### Parallel Processing

```bash
# Number of parallel workers for evidence gathering (default: 5)
MAX_WORKERS=5

# Timeout for evidence searches in seconds (default: 30)
SEARCH_TIMEOUT=30
```

### Rate Limiting

```bash
# Rate limit delay between API calls in seconds (default: 1.0)
API_RATE_LIMIT_DELAY=1.0

# Max retries for failed API calls (default: 3)
MAX_API_RETRIES=3
```

### Caching

```bash
# Enable caching of API responses (default: true)
ENABLE_CACHING=true

# Cache directory (default: .cache)
CACHE_DIR=.cache

# Cache expiry in hours (default: 24)
CACHE_EXPIRY_HOURS=24
```

---

## Development & Debugging

### Debug Mode

```bash
# Enable debug mode (verbose logging, no caching)
DEBUG=true
```

**Effects:**
- Sets `LOG_LEVEL=DEBUG`
- Disables caching
- Enables request/response logging
- Saves intermediate outputs

### Test Mode

```bash
# Use test/mock data instead of real APIs
TEST_MODE=true

# Mock data directory
MOCK_DATA_DIR=tests/mock_data
```

### Dry Run

```bash
# Simulate run without API calls (for testing)
DRY_RUN=true
```

---

## Example Configurations

### Minimal (Required Only)

```bash
# .env.minimal
GOOGLE_CLOUD_PROJECT=your-project-id
PROJECT_ID=your-project-id
LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
```

### Recommended (Optimal Performance)

```bash
# .env.recommended
GOOGLE_CLOUD_PROJECT=your-project-id
PROJECT_ID=your-project-id
LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json

# Optional APIs (recommended)
GOOGLE_API_KEY=AIza...
GOOGLE_CSE_ID=your-cse-id
YOUTUBE_API_KEY=AIza...

# Optimal settings
VERTEX_MODEL_NAME=gemini-2.5-flash
MAX_OUTPUT_TOKENS_2_5_FLASH=65536
THINKING_BUDGET=0
SEGMENT_FPS=1.0

# Intelligent segmentation (leave commented)
#SEGMENT_DURATION_SECONDS=3000

LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
```

### Debug (Maximum Verbosity)

```bash
# .env.debug
GOOGLE_CLOUD_PROJECT=your-project-id
PROJECT_ID=your-project-id
LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json

# Debug settings
DEBUG=true
LOG_LEVEL=DEBUG
LOG_TO_FILE=true
LOG_TO_CONSOLE=true
PYTHONUNBUFFERED=1

# Short segments for faster iteration
SEGMENT_DURATION_SECONDS=300  # 5 minutes
```

### Production (Cloud Run)

```bash
# .env.production
GOOGLE_CLOUD_PROJECT=your-project-id
PROJECT_ID=your-project-id
LOCATION=us-central1

# Production settings
DEPLOYMENT_MODE=production
STORAGE_BACKEND=gcs
GCS_BUCKET_NAME=verityngn-reports

# Optimized for cloud
VERTEX_MODEL_NAME=gemini-2.5-flash
MAX_WORKERS=10
API_RATE_LIMIT_DELAY=0.5

LOG_LEVEL=INFO
ENABLE_CACHING=true
```

---

## Configuration Validation

### Test Configuration

```bash
python test_credentials.py
```

Expected output:

```
✅ Google Cloud Project: your-project-id
✅ Vertex AI Authentication: SUCCESS
✅ All required credentials configured!
```

### Check Environment

```bash
./check_env_complete.sh
```

Validates:
- `.env` file exists
- Required variables set
- Service account file exists
- File permissions correct

---

## Configuration Priority

Variables can be set in multiple places. Priority (highest first):

1. **Environment variables** (explicitly set in shell)
2. **`.env` file** (project root)
3. **Default values** (in code)

Example:

```bash
# Priority 1: Shell environment (highest)
export VERTEX_MODEL_NAME=gemini-1.5-pro

# Priority 2: .env file (medium)
# VERTEX_MODEL_NAME=gemini-2.5-flash

# Priority 3: Default in code (lowest)
# VERTEX_MODEL_NAME = os.getenv("VERTEX_MODEL_NAME", "gemini-2.5-flash")
```

---

## Security Best Practices

### Never Commit Credentials

```bash
# .gitignore already includes:
.env
.env.*
*.json  # Service account files
```

### Restrict File Permissions

```bash
# Make service account file readable only by owner
chmod 600 service-account.json

# Make .env file readable only by owner
chmod 600 .env
```

### Use Environment-Specific Files

```bash
.env.development
.env.staging
.env.production
```

Load based on environment:

```python
import os
from dotenv import load_dotenv

env = os.getenv("ENVIRONMENT", "development")
load_dotenv(f".env.{env}")
```

---

## Next Steps

- **[Setup Guide](../guides/SETUP.md)** - Complete setup instructions
- **[Architecture](../ARCHITECTURE.md)** - Technical architecture details
- **[Testing Guide](../guides/TESTING.md)** - Test your configuration

---

**Last Updated:** October 28, 2025  
**Version:** 2.0

