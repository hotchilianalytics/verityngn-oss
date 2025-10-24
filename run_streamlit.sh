#!/bin/bash
#
# run_streamlit.sh - Start Streamlit with proper Google Cloud credentials
#
# This script loads environment variables from .env and starts the Streamlit UI.
#
# Prerequisites:
# 1. Copy .env.example to .env
# 2. Fill in your GOOGLE_APPLICATION_CREDENTIALS path in .env
# 3. Run this script
#

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
else
    echo "⚠️  Warning: .env file not found!"
    echo "📝 Please create .env from .env.example and configure your credentials."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if GOOGLE_APPLICATION_CREDENTIALS is set
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "❌ Error: GOOGLE_APPLICATION_CREDENTIALS not set in .env"
    echo "📝 Please set GOOGLE_APPLICATION_CREDENTIALS in your .env file"
    exit 1
fi

echo "================================================================================================"
echo "🚀 Starting VerityNgn Streamlit UI"
echo "================================================================================================"
echo ""
echo "📁 Credentials: $GOOGLE_APPLICATION_CREDENTIALS"
echo "🌐 URL: http://localhost:8501"
echo ""
echo "================================================================================================"
echo ""

# Start Streamlit
streamlit run ui/streamlit_app.py

