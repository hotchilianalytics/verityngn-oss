#!/bin/bash
# Check if all required environment variables are set for VerityNgn

echo "🔍 Checking VerityNgn Environment Variables"
echo "=========================================="
echo ""

# Load .env if it exists
if [ -f .env ]; then
    echo "✅ Found .env file"
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ No .env file found"
    exit 1
fi

echo ""
echo "Checking required variables..."
echo ""

errors=0

# Check GOOGLE_APPLICATION_CREDENTIALS
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "✅ GOOGLE_APPLICATION_CREDENTIALS: $GOOGLE_APPLICATION_CREDENTIALS"
    else
        echo "❌ GOOGLE_APPLICATION_CREDENTIALS file not found: $GOOGLE_APPLICATION_CREDENTIALS"
        errors=$((errors + 1))
    fi
else
    echo "❌ GOOGLE_APPLICATION_CREDENTIALS not set"
    errors=$((errors + 1))
fi

# Check GOOGLE_CLOUD_PROJECT or PROJECT_ID
if [ -n "$GOOGLE_CLOUD_PROJECT" ] || [ -n "$PROJECT_ID" ]; then
    project="${GOOGLE_CLOUD_PROJECT:-$PROJECT_ID}"
    echo "✅ Project ID: $project"
else
    echo "❌ GOOGLE_CLOUD_PROJECT or PROJECT_ID not set"
    echo "   Add to .env: GOOGLE_CLOUD_PROJECT=your-project-id"
    errors=$((errors + 1))
fi

# Check LOCATION
if [ -n "$LOCATION" ]; then
    echo "✅ Location: $LOCATION"
else
    echo "⚠️  LOCATION not set (will default to us-central1)"
fi

echo ""
echo "Optional variables:"
echo ""

# Check YouTube API Key
if [ -n "$YOUTUBE_API_KEY" ]; then
    echo "✅ YOUTUBE_API_KEY: ${YOUTUBE_API_KEY:0:10}..."
else
    echo "⚠️  YOUTUBE_API_KEY not set (will use yt-dlp fallback)"
fi

# Check Google Search API
if [ -n "$GOOGLE_SEARCH_API_KEY" ] || [ -n "$GOOGLE_API_KEY" ]; then
    key="${GOOGLE_SEARCH_API_KEY:-$GOOGLE_API_KEY}"
    echo "✅ Google Search API Key: ${key:0:10}..."
else
    echo "⚠️  GOOGLE_SEARCH_API_KEY not set (limited web search)"
fi

# Check CSE ID
if [ -n "$GOOGLE_CSE_ID" ] || [ -n "$CSE_ID" ]; then
    cse="${GOOGLE_CSE_ID:-$CSE_ID}"
    echo "✅ Custom Search Engine ID: ${cse:0:10}..."
else
    echo "⚠️  GOOGLE_CSE_ID not set (limited web search)"
fi

echo ""
echo "=========================================="

if [ $errors -eq 0 ]; then
    echo "✅ All required variables are set!"
    echo ""
    echo "You can now run: python test_tl_video.py"
    exit 0
else
    echo "❌ $errors required variable(s) missing"
    echo ""
    echo "Please add the missing variables to your .env file"
    exit 1
fi








