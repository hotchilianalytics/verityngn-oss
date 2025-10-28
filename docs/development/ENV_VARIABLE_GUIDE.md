# Environment Variable Guide

Your `.env` file should be at `/Users/ajjc/proj/verityngn-oss/.env`.

## Required Variable Names

The VerityNgn system checks for these **exact** variable names:

### Google Search API (for claim verification)

```bash
# The code looks for these (in order of priority):
GOOGLE_SEARCH_API_KEY=AIza...
GOOGLE_API_KEY=AIza...         # Alternative (also used by genai client)
GOOGLE_AI_STUDIO_KEY=AIza...   # Fallback
```

**Used by:**

- `verityngn/services/search/web_search.py` - Web search for verification
- `verityngn/workflows/analysis.py` - genai client initialization

### Custom Search Engine ID

```bash
# The code looks for these:
CSE_ID=your-search-engine-id
GOOGLE_CSE_ID=your-search-engine-id  # Alternative
```

**Used by:**

- `verityngn/services/search/web_search.py` - Web search configuration

### YouTube Data API

```bash
YOUTUBE_API_KEY=AIza...
```

**Fallback:** If not set, defaults to `GOOGLE_SEARCH_API_KEY` value (see `settings.py` line 105)

**Used by:**

- `verityngn/workflows/analysis.py` - Metadata extraction
- YouTube counter-intelligence searches

---

## Your .env File Should Look Like

```bash
# Required for basic operation
GOOGLE_CLOUD_PROJECT=your-project-id
PROJECT_ID=your-project-id

# Optional: For web search verification
GOOGLE_SEARCH_API_KEY=AIza...
CSE_ID=your-search-engine-id

# Optional: For YouTube features  
YOUTUBE_API_KEY=AIza...

# Optional: For genai client (if using AI Studio)
GOOGLE_AI_STUDIO_KEY=AIza...
```

---

## Check What You Have

Run the test script to see what's loaded:

```bash
cd /Users/ajjc/proj/verityngn-oss
python test_credentials.py
```

This will:

1. Try to load your `.env` file
2. Show which variables are set
3. Display the first 10 characters of each key (for verification)

---

## If Variables Are Not Loading

### Option 1: Check variable names in your .env

Open your `.env` file and verify the variable names **exactly match** those above:

```bash
# ✅ CORRECT
GOOGLE_SEARCH_API_KEY=AIza...
CSE_ID=a1b2c3d4e...

# ❌ WRONG (won't be recognized)
GOOGLE_API_KEY_SEARCH=AIza...
CUSTOM_SEARCH_ENGINE_ID=a1b2c3d4e...
```

### Option 2: Check .env file location

The `.env` file must be at:

```
/Users/ajjc/proj/verityngn-oss/.env
```

NOT at:

- `/Users/ajjc/proj/verityngn/.env` (different repo)
- `/Users/ajjc/.env` (home directory)
- `/Users/ajjc/proj/verityngn-oss/verityngn/.env` (subdirectory)

### Option 3: Verify python-dotenv is installed

```bash
pip list | grep python-dotenv
```

If not installed:

```bash
pip install python-dotenv
```

It's already in `requirements.txt`, so should be installed.

---

## Alternative: Use Export Commands

If you prefer not to use `.env`, you can export directly:

```bash
export GOOGLE_SEARCH_API_KEY="AIza..."
export CSE_ID="a1b2c3d4e..."
export YOUTUBE_API_KEY="AIza..."
```

**To persist across sessions**, add to `~/.zshrc`:

```bash
echo 'export GOOGLE_SEARCH_API_KEY="AIza..."' >> ~/.zshrc
echo 'export CSE_ID="a1b2c3d4e..."' >> ~/.zshrc
echo 'export YOUTUBE_API_KEY="AIza..."' >> ~/.zshrc
source ~/.zshrc
```

---

## Verify It Works

After setting your variables, run:

```bash
cd /Users/ajjc/proj/verityngn-oss
python test_credentials.py
```

Expected output:

```
4️⃣  Testing optional APIs...
   📄 Loaded .env from /Users/ajjc/proj/verityngn-oss/.env
   ✅ Google Search API Key: AIzaSyC-12...
   ✅ Google CSE ID: a1b2c3d4e5...
   ✅ YouTube API Key: AIzaSyC-12...
```

---

## What Each API Enables

| Variable | Without It | With It |
|----------|-----------|---------|
| `GOOGLE_SEARCH_API_KEY` | Limited verification, no web search | ✅ Full claim verification with web sources |
| `CSE_ID` | Can't search the web | ✅ Custom Search returns relevant results |
| `YOUTUBE_API_KEY` | Uses yt-dlp fallback | ✅ Better metadata + YouTube counter-intel |

**All three are OPTIONAL** - the system works without them, but with reduced features.

---

## Need Help?

1. **Check your current .env:**

   ```bash
   cat /Users/ajjc/proj/verityngn-oss/.env
   ```

2. **Test variable loading:**

   ```bash
   python test_credentials.py
   ```

3. **See what's loaded:**

   ```bash
   python -c "import os; from dotenv import load_dotenv; from pathlib import Path; load_dotenv(Path('.')/ '.env'); print('GOOGLE_SEARCH_API_KEY:', os.getenv('GOOGLE_SEARCH_API_KEY', 'NOT SET')[:20])"
   ```


