#!/bin/bash
# VerityNgn Optional API Keys Setup
# Run: source set_api_keys.sh

echo "🔑 Setting up optional API keys for VerityNgn..."

# Google Search API (for claim verification)
read -p "Enter GOOGLE_API_KEY (press Enter to skip): " google_key
if [ ! -z "$google_key" ]; then
    export GOOGLE_API_KEY="$google_key"
    echo "✅ GOOGLE_API_KEY set"
else
    echo "⚠️  GOOGLE_API_KEY skipped"
fi

# Custom Search Engine ID
read -p "Enter GOOGLE_CSE_ID (press Enter to skip): " cse_id
if [ ! -z "$cse_id" ]; then
    export GOOGLE_CSE_ID="$cse_id"
    echo "✅ GOOGLE_CSE_ID set"
else
    echo "⚠️  GOOGLE_CSE_ID skipped"
fi

# YouTube Data API
read -p "Enter YOUTUBE_API_KEY (or same as GOOGLE_API_KEY, press Enter to skip): " yt_key
if [ ! -z "$yt_key" ]; then
    export YOUTUBE_API_KEY="$yt_key"
    echo "✅ YOUTUBE_API_KEY set"
else
    echo "⚠️  YOUTUBE_API_KEY skipped"
fi

echo ""
echo "📋 Current API Keys Status:"
echo "   GOOGLE_API_KEY: ${GOOGLE_API_KEY:+SET ✅}"
echo "   GOOGLE_API_KEY: ${GOOGLE_API_KEY:-NOT SET ⚠️}"
echo "   GOOGLE_CSE_ID: ${GOOGLE_CSE_ID:+SET ✅}"
echo "   GOOGLE_CSE_ID: ${GOOGLE_CSE_ID:-NOT SET ⚠️}"
echo "   YOUTUBE_API_KEY: ${YOUTUBE_API_KEY:+SET ✅}"
echo "   YOUTUBE_API_KEY: ${YOUTUBE_API_KEY:-NOT SET ⚠️}"
echo ""
echo "💡 To persist these across sessions, add them to ~/.zshrc:"
echo "   echo 'export GOOGLE_API_KEY=\"$GOOGLE_API_KEY\"' >> ~/.zshrc"
echo "   echo 'export GOOGLE_CSE_ID=\"$GOOGLE_CSE_ID\"' >> ~/.zshrc"
echo "   echo 'export YOUTUBE_API_KEY=\"$YOUTUBE_API_KEY\"' >> ~/.zshrc"



