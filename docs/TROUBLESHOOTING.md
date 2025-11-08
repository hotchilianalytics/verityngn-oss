# VerityNgn Troubleshooting Guide

Solutions to common issues and debugging strategies.

---

## Quick Diagnostics

### Run Diagnostic Script

```bash
python test_credentials.py
```

This checks:
- ✅ Google Cloud project configuration
- ✅ Vertex AI authentication
- ✅ Service account setup
- ✅ API key configuration

---

## Authentication Issues

### Error: "Could not automatically determine credentials"

**Symptoms:**
```
DefaultCredentialsError: Could not automatically determine credentials
```

**Causes:**
1. No service account JSON file
2. `GOOGLE_APPLICATION_CREDENTIALS` not set
3. No application default credentials

**Solutions:**

**Option 1: Use Service Account**

```bash
# 1. Download service account JSON from Google Cloud Console
# 2. Place in project root as service-account.json
# 3. Set environment variable:
export GOOGLE_APPLICATION_CREDENTIALS="./service-account.json"

# 4. Or add to .env file:
echo "GOOGLE_APPLICATION_CREDENTIALS=./service-account.json" >> .env
```

**Option 2: Use Application Default Credentials**

```bash
gcloud auth application-default login
```

**Option 3: Check .env File**

```bash
# Verify .env file exists and has correct format
cat .env

# Should contain:
# GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
# GOOGLE_CLOUD_PROJECT=your-project-id
# PROJECT_ID=your-project-id
```

### Error: "Reauthentication is needed"

**Symptoms:**
```
google.auth.exceptions.RefreshError: Reauthentication is needed
```

**Cause:** OAuth2 credentials expired

**Solution 1: Switch to Service Account**

```bash
# Create service account and download JSON key
export GOOGLE_APPLICATION_CREDENTIALS="./service-account.json"
```

**Solution 2: Re-authenticate**

```bash
gcloud auth application-default login
```

**Solution 3: Remove old credentials**

```bash
# macOS/Linux
rm ~/.config/gcloud/application_default_credentials.json

# Re-authenticate
gcloud auth application-default login
```

### Error: "Permission denied for Vertex AI"

**Symptoms:**
```
403 Permission denied on resource project
```

**Cause:** Service account lacks Vertex AI permissions

**Solution:**

```bash
# Grant Vertex AI User role
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
    --member="serviceAccount:SERVICE-ACCOUNT-EMAIL" \
    --role="roles/aiplatform.user"

# Verify permissions
gcloud projects get-iam-policy YOUR-PROJECT-ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:SERVICE-ACCOUNT-EMAIL"
```

---

## Processing Issues

### Issue: "Process seems hung / no progress"

**Symptoms:**
- No log output for 10+ minutes
- Last message: "Processing segment..."
- Terminal appears frozen

**Is it really hung?**

**✅ NORMAL BEHAVIOR:**
- 8-12 minutes of no output during segment processing
- Multimodal analysis is compute-intensive
- No progress bars during LLM processing

**🔍 How to check:**

1. **Check timestamp** - Has it been < 15 minutes?
   - If YES: **Wait** - this is normal!
   - If NO: May be hung, proceed to debugging

2. **Look for last log message:**
   ```
   🎬 [VERTEX] Segment 1/1: Processing 0s → 1998s (33.3 minutes)
   ⏱️  Expected processing time: 8-12 minutes for this segment
   ```
   - If you see this: **Wait 12 minutes** before worrying

3. **Check expected time:**
   - 33-minute video: ~10 minutes processing time
   - 60-minute video: ~20 minutes processing time

**❌ ACTUALLY HUNG (after 15+ minutes):**

**Debug steps:**

```bash
# 1. Check network connection
ping google.com

# 2. Check Google Cloud API status
# Visit: https://status.cloud.google.com/

# 3. Check API quotas
gcloud services quota list --service=aiplatform.googleapis.com --project=YOUR-PROJECT-ID

# 4. Try with shorter video first (< 10 minutes)
python -m verityngn.workflows.main_workflow --url "https://www.youtube.com/watch?v=SHORT_VIDEO_ID"

# 5. Enable debug logging
export PYTHONUNBUFFERED=1
python test_tl_video.py 2>&1 | tee debug.log
```

**Workaround: Force shorter segments**

```bash
# Add to .env file:
SEGMENT_DURATION_SECONDS=1800  # 30 minutes instead of 50
```

### Issue: "Empty response from segmented Vertex YouTube analysis"

**Symptoms:**
```
WARNING - Empty response from segmented Vertex YouTube analysis
```

**Causes:**
1. Segment too large for context window
2. Network timeout
3. API rate limiting
4. Invalid video URL

**Solutions:**

**1. Reduce segment size:**

```bash
# In .env file:
SEGMENT_DURATION_SECONDS=1800  # 30 minutes

# Or for debugging:
SEGMENT_DURATION_SECONDS=300   # 5 minutes
```

**2. Check network:**

```bash
# Test connectivity
curl -I https://aiplatform.googleapis.com

# Check DNS resolution
nslookup aiplatform.googleapis.com
```

**3. Verify video URL:**

```python
# Test video URL directly
from yt_dlp import YoutubeDL

ydl = YoutubeDL({'quiet': True})
info = ydl.extract_info("https://www.youtube.com/watch?v=VIDEO_ID", download=False)
print(f"Duration: {info['duration']}s")
```

**4. Check API quotas:**

```bash
gcloud services quota list \
    --service=aiplatform.googleapis.com \
    --project=YOUR-PROJECT-ID \
    --filter="metric.type=aiplatform.googleapis.com/online_prediction_requests_per_base_model"
```

### Issue: Slow processing (> 30 minutes for 33-minute video)

**Expected times (v2.0):**
- 10-minute video: 8-12 minutes
- 33-minute video: 8-12 minutes  
- 60-minute video: 16-24 minutes

**If slower:**

**Check segmentation:**

```bash
# Look for this in logs:
🎬 [VERTEX] Segmentation plan: 1998s video → X segment(s)

# Should be:
# 33-minute video → 1 segment (optimal)
# 60-minute video → 2 segments (optimal)

# If seeing many segments (5-7+), check .env:
cat .env | grep SEGMENT_DURATION_SECONDS

# Should be commented out or unset for intelligent calculation:
# #SEGMENT_DURATION_SECONDS=3000
```

**Force intelligent segmentation:**

```bash
# In .env file, comment out or remove:
#SEGMENT_DURATION_SECONDS=3000

# System will auto-calculate optimal segments
```

---

## Dependency Issues

### Error: "ModuleNotFoundError: No module named 'psutil'"

**Solution:**

```bash
pip install psutil
```

Or use conda environment:

```bash
conda env create -f environment.yml
conda activate verityngn
```

### Error: "ModuleNotFoundError: No module named 'isodate'"

**Solution:**

```bash
pip install isodate
```

### Error: "ModuleNotFoundError: No module named 'dotenv'"

**Solution:**

```bash
pip install python-dotenv
```

### Error: "ModuleNotFoundError: No module named 'verityngn...'"

**Cause:** Missing internal modules or incorrect Python path

**Solution:**

```bash
# 1. Ensure you're in project root
cd /path/to/verityngn-oss

# 2. Install in development mode
pip install -e .

# 3. Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/verityngn-oss"
```

---

## Video Download Issues

### Error: yt-dlp cache permission error

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/Users/username/.cache/yt-dlp'
```

**Solution:**

```bash
# Fix cache permissions
chmod -R 755 ~/.cache/yt-dlp

# Or clear cache
rm -rf ~/.cache/yt-dlp
```

### Error: Video unavailable

**Symptoms:**
```
ERROR: Video unavailable
```

**Causes:**
1. Private video
2. Age-restricted video
3. Region-locked video
4. Invalid URL

**Solutions:**

```bash
# Test URL with yt-dlp directly
yt-dlp --get-title "https://www.youtube.com/watch?v=VIDEO_ID"

# For age-restricted videos, use cookies:
yt-dlp --cookies cookies.txt "URL"
```

---

## API Key Issues

### Warning: "Google Search API key or CSE ID not configured"

**Impact:** Limited evidence verification capabilities

**Severity:** ⚠️ Low (optional feature)

**Solution (optional):**

```bash
# Add to .env file:
GOOGLE_API_KEY=AIza...
GOOGLE_CSE_ID=your-cse-id
```

**Or accept reduced functionality** - system works without it.

### Warning: "YouTube API key not configured"

**Impact:** Uses yt-dlp fallback (slower)

**Severity:** ⚠️ Low (automatic fallback)

**Solution (optional):**

```bash
# Add to .env file:
YOUTUBE_API_KEY=AIza...
```

**Or accept fallback** - yt-dlp works fine, just slower.

---

## Debugging Strategies

### Enable Verbose Logging

```bash
# Set unbuffered output
export PYTHONUNBUFFERED=1

# Run with full logging
python test_tl_video.py 2>&1 | tee debug.log

# Review logs
cat debug.log | grep ERROR
cat debug.log | grep WARNING
```

### Use VS Code Debugger

1. **Open** `.vscode/launch.json` (already configured)

2. **Set breakpoints** in code

3. **Run debugger:**
   - Press F5
   - Select "Debug: Test TL Video"
   - Step through execution

4. **Inspect variables:**
   - Check `video_duration_seconds`
   - Check `SEGMENT_DURATION_SECONDS`
   - Check API responses

### Test Components Individually

**Test segmentation only:**

```bash
python debug_segmented_analysis.py
```

**Test claims extraction only:**

```bash
python test_enhanced_claims.py
```

**Test credentials only:**

```bash
python test_credentials.py
```

**Test video download only:**

```bash
python -c "
from yt_dlp import YoutubeDL
ydl = YoutubeDL({'quiet': True})
info = ydl.extract_info('https://www.youtube.com/watch?v=VIDEO_ID', download=False)
print(f'Title: {info[\"title\"]}')
print(f'Duration: {info[\"duration\"]}s')
"
```

### Check Environment

```bash
# Run environment check
./check_env_complete.sh
```

Expected output:

```
✅ .env file exists
✅ GOOGLE_APPLICATION_CREDENTIALS set
✅ GOOGLE_CLOUD_PROJECT set
✅ Service account file exists
✅ All required environment variables configured
```

---

## Performance Optimization

### Reduce API Costs

**Use intelligent segmentation** (automatic):

```bash
# In .env, leave commented:
#SEGMENT_DURATION_SECONDS=3000

# System auto-calculates optimal segments
```

**Results:**
- 33-minute video: 1 API call instead of 7 (86% reduction)
- 60-minute video: 2 API calls instead of 12 (83% reduction)

### Speed Up Processing

**1. Use Gemini 2.5 Flash** (default):

```bash
# In .env:
VERTEX_MODEL_NAME=gemini-2.5-flash
```

**2. Disable thinking budget:**

```bash
# In .env:
THINKING_BUDGET=0
```

**3. Optimize segment FPS:**

```bash
# 1 FPS is optimal (default)
SEGMENT_FPS=1.0

# Don't increase unless needed
```

---

## Common Error Messages

### "json_lib is not defined"

**Status:** ✅ Fixed in current version

**If you see this:** Update to latest version

```bash
git pull origin main
pip install -r requirements.txt
```

### "cannot access local variable 'json_lib'"

**Status:** ✅ Fixed in current version

**If you see this:** Update to latest version

### "404 Not Found" from Vertex AI

**Cause:** Model name incorrect or not available in region

**Solution:**

```bash
# Check .env for correct model name:
VERTEX_MODEL_NAME=gemini-2.5-flash  # Correct
# Not: gemini-2.5-flash-001 or other variants

# Verify model is available in your region:
gcloud ai models list --region=us-central1 --filter="displayName:gemini"
```

---

## Getting Help

### Check Documentation

1. **[Setup Guide](guides/SETUP.md)** - Authentication and installation
2. **[Quick Start](guides/QUICK_START.md)** - First-time usage
3. **[Architecture](ARCHITECTURE.md)** - Technical details
4. **[Testing Guide](guides/TESTING.md)** - Testing and validation

### Collect Debug Information

Before reporting issues, collect:

```bash
# 1. System information
uname -a
python --version

# 2. Environment check
./check_env_complete.sh > env_check.txt

# 3. Credentials test
python test_credentials.py > creds_test.txt

# 4. Full debug log
PYTHONUNBUFFERED=1 python test_tl_video.py 2>&1 | tee full_debug.log

# 5. Package versions
pip list > requirements_actual.txt
```

### Report Issues

When reporting issues, include:

- Error message (full traceback)
- Steps to reproduce
- Expected vs actual behavior
- Environment information (from above)
- Video URL (if applicable and public)

---

**Last Updated:** October 28, 2025  
**Version:** 2.0








