# Quick Test - tLJC8hkK-ao Video

## One-Line Quick Start

```bash
python test_tl_video.py
```

## What It Does

Runs complete VerityNgn verification on LIPOZEM video (tLJC8hkK-ao):
- Downloads video
- Analyzes content with multimodal LLM
- Extracts claims
- Verifies with web search
- Generates truthfulness report

## Output Location

```
outputs/tLJC8hkK-ao/report.html
```

## Expected Time

⏱️ 10-15 minutes

## Prerequisites

```bash
# 1. Set credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export YOUTUBE_API_KEY="your_youtube_api_key"

# 2. Activate environment
conda activate verityngn

# 3. Run test
python test_tl_video.py
```

## View Results

```bash
# Open HTML report
open outputs/tLJC8hkK-ao/report.html

# Or view JSON
cat outputs/tLJC8hkK-ao/report.json | jq .
```

That's it! 🎉

For detailed documentation, see `TEST_TL_VIDEO_USAGE.md`


