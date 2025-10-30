#!/bin/bash
# Run test with proper credential setup

set -e  # Exit on error

echo "🔐 Setting up credentials..."

# Set the service account JSON path
export GOOGLE_APPLICATION_CREDENTIALS="/Users/ajjc/proj/verityngn-oss/verityngn/config/verityindex-0-0-1-6a21e94ca0a3.json"

# Set Google Cloud project
export GOOGLE_CLOUD_PROJECT="verityindex-0-0-1"
export PROJECT_ID="verityindex-0-0-1"
export LOCATION="us-central1"

# Load .env file if it exists (for API keys)
if [ -f ".env" ]; then
    echo "📄 Loading .env file..."
    # Export all variables from .env
    set -a
    source .env
    set +a
else
    echo "⚠️  No .env file found - API keys may be missing"
    echo "   Google Search API: Will use fallback"
    echo "   YouTube API: Will use fallback"
fi

# Verify service account JSON exists
if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "❌ Service account JSON not found at: $GOOGLE_APPLICATION_CREDENTIALS"
    exit 1
fi

echo "✅ Service account: verityindex-sa-research@verityindex-0-0-1.iam.gserviceaccount.com"
echo "✅ Project: $GOOGLE_CLOUD_PROJECT"

# Show what's configured
echo ""
echo "🔍 Configuration status:"
if [ -n "$GOOGLE_SEARCH_API_KEY" ]; then
    echo "  ✅ Google Search API Key: Configured"
else
    echo "  ⚠️  Google Search API Key: Not configured (searches will fail)"
fi

if [ -n "$CSE_ID" ]; then
    echo "  ✅ Custom Search Engine ID: Configured"
else
    echo "  ⚠️  Custom Search Engine ID: Not configured (searches will fail)"
fi

if [ -n "$YOUTUBE_API_KEY" ]; then
    echo "  ✅ YouTube API Key: Configured"
else
    echo "  ⚠️  YouTube API Key: Not configured (will use fallback)"
fi

echo ""
echo "🚀 Running hang fix test suite..."
echo ""

# Run the test with full flag if requested
if [ "$1" = "--full-test" ] || [ "$1" = "-f" ]; then
    python test_hang_fix.py --full-test
else
    python test_hang_fix.py
fi

