# Test tLJC8hkK-ao Video - Usage Guide

## Overview

This script (`test_tl_video.py`) runs the complete VerityNgn verification workflow on the LIPOZEM video (tLJC8hkK-ao) outside of the Streamlit UI.

## Video Details

- **Video ID**: tLJC8hkK-ao
- **Title**: [LIPOZEM] Exclusive Interview with Dr. Julian Ross
- **Duration**: ~33 minutes
- **Type**: Product promotion video (weight loss supplement)

## What This Script Does

The script runs the complete 7-stage verification pipeline:

1. **Video Download** - Downloads video, audio, and extracts metadata/transcript
2. **Initial Analysis** - Multimodal LLM analysis of video content
3. **Counter-Intelligence** - Searches YouTube for reviews, debunks, and contradictory content
4. **Claim Extraction** - Extracts verifiable claims from the video
5. **Claim Verification** - Web search and evidence gathering for each claim
6. **Report Generation** - Calculates truthfulness scores
7. **Save Reports** - Generates JSON, Markdown, and HTML reports

## Prerequisites

Before running, ensure you have:

1. **Environment Variables Set**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
   export YOUTUBE_API_KEY="your_youtube_api_key"
   ```

2. **Dependencies Installed**:
   ```bash
   conda env create -f environment.yml
   conda activate verityngn
   # OR
   pip install -r requirements.txt
   ```

3. **FFmpeg Installed** (for video processing):
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   ```

## Running the Test

### Basic Usage

```bash
python test_tl_video.py
```

### With Conda Environment

```bash
conda activate verityngn
python test_tl_video.py
```

### Expected Runtime

- **Total Time**: 10-15 minutes (depending on network speed and API response times)
- Stage breakdown:
  - Video Download: 1-2 minutes
  - Initial Analysis: 2-3 minutes
  - Counter-Intelligence: 1-2 minutes
  - Claim Verification: 5-10 minutes (depends on number of claims)
  - Report Generation: 1 minute

## Output

### Location

All outputs are saved to:
```
outputs/tLJC8hkK-ao/
```

### Generated Files

- `report.json` - Complete verification report in JSON format
- `report.md` - Markdown-formatted report
- `report.html` - HTML report with embedded video and interactive elements
- `video.mp4` - Downloaded video file
- `transcript.vtt` - Video transcript
- `metadata.json` - Video metadata

### Console Output

The script provides detailed logging of each stage:

```
================================================================================
🚀 VERITYNGN WORKFLOW TEST - tLJC8hkK-ao (LIPOZEM)
================================================================================
📹 Video ID: tLJC8hkK-ao
🔗 Video URL: https://www.youtube.com/watch?v=tLJC8hkK-ao

📦 Importing verification workflow...
✅ Modules imported successfully

🏗️ Starting verification workflow...
    This will take several minutes to complete.

Pipeline stages:
  1. 📥 Video Download (download + metadata extraction)
  2. 🎬 Initial Analysis (multimodal LLM analysis)
  3. 🔍 Counter-Intelligence (YouTube search for reviews/debunks)
  4. 📋 Claim Extraction (extract and filter claims)
  5. ✅ Claim Verification (web search + evidence gathering)
  6. 📊 Report Generation (truthfulness scoring)
  7. 💾 Save Reports (JSON + Markdown + HTML)

[... detailed stage logging ...]

================================================================================
✅ WORKFLOW COMPLETED SUCCESSFULLY!
================================================================================

📊 RESULTS SUMMARY
--------------------------------------------------------------------------------
   Truthfulness Score: 42.5
   Claims Verified: 15
   Output Directory: outputs/tLJC8hkK-ao

📁 Generated Files:
   - report.html (245.3 KB)
   - report.json (128.7 KB)
   - report.md (89.2 KB)
   - transcript.vtt (45.1 KB)
   - metadata.json (12.3 KB)
   - video.mp4 (125437.8 KB)

🎉 Test completed successfully!
📂 View full report at: outputs/tLJC8hkK-ao/report.html
```

## Viewing Results

### HTML Report

Open the HTML report in your browser:

```bash
open outputs/tLJC8hkK-ao/report.html
# OR
firefox outputs/tLJC8hkK-ao/report.html
```

### JSON Report

View the JSON report for programmatic access:

```bash
cat outputs/tLJC8hkK-ao/report.json | jq .
```

### Markdown Report

View the markdown report:

```bash
cat outputs/tLJC8hkK-ao/report.md
```

## Troubleshooting

### "Could not extract video ID from URL"

- Ensure you have internet connectivity
- Check that YouTube is accessible from your location

### "Authentication failed"

- Verify `GOOGLE_APPLICATION_CREDENTIALS` is set correctly
- Ensure the service account has Vertex AI permissions
- Run: `python test_credentials.py` to verify credentials

### "YouTube API quota exceeded"

- The YouTube Data API has daily quota limits
- Wait 24 hours or use a different API key
- Counter-intelligence features will be limited without YouTube API access

### "FFmpeg not found"

- Install FFmpeg as described in Prerequisites
- Verify installation: `ffmpeg -version`

### Out of Memory

- The multimodal analysis processes video frames and can be memory-intensive
- Ensure you have at least 4GB of free RAM
- Close other memory-intensive applications

## Differences from Streamlit UI

This script runs the **same verification pipeline** as the Streamlit UI, but:

✅ **Advantages**:
- No browser required
- Better for automated testing
- Easier to integrate into CI/CD pipelines
- Complete console logging
- Can run on headless servers

❌ **Limitations**:
- No real-time progress visualization
- No interactive configuration UI
- Must edit script to change video URL

## Customization

To test a different video, edit the script:

```python
# Change these lines in run_tl_video_test():
video_id = "your_video_id"
video_url = f"https://www.youtube.com/watch?v=&#123;video_id&#125;"
```

Or create a more flexible version:

```python
import sys

def run_video_test(video_url):
    from verityngn.workflows.pipeline import run_verification
    final_state, output_dir = run_verification(video_url)
    return final_state, output_dir

if __name__ == "__main__":
    if len(sys.argv) &lt; 2:
        print("Usage: python test_video.py [youtube_url]")
        sys.exit(1)
    
    video_url = sys.argv[1]
    run_video_test(video_url)
```

## Related Files

- `test_enhanced_claims.py` - Tests just the claim extraction stage
- `validate_with_existing_data.py` - Validates against existing analysis
- `run_streamlit.sh` - Runs the Streamlit UI version

## Support

For issues or questions:
1. Check the main README.md
2. Review TROUBLESHOOTING.md
3. Check logs in `outputs/tLJC8hkK-ao/`


