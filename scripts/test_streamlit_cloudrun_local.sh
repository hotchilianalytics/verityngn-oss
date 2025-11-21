#!/bin/bash
# Quick test script for Streamlit Cloud Run mode locally

set -e

echo "🧪 Testing Streamlit Cloud Run Mode Locally"
echo ""

# Set Cloud Run API URL
export CLOUDRUN_API_URL="https://verityngn-api-ze7rxua3dq-uc.a.run.app"

echo "✅ Set CLOUDRUN_API_URL=$CLOUDRUN_API_URL"
echo ""
echo "Starting Streamlit..."
echo ""
echo "📋 Test Checklist:"
echo "  1. Open browser to http://localhost:8501"
echo "  2. Check sidebar for 'Backend Mode' selector"
echo "  3. Select '☁️ Cloud Run + Batch' mode"
echo "  4. Enter a YouTube URL (e.g., https://www.youtube.com/watch?v=jNQXAC9IVRw)"
echo "  5. Click 'Start Verification'"
echo "  6. Switch to 'Processing' tab to monitor status"
echo ""
echo "Press Ctrl+C to stop Streamlit"
echo ""

cd "$(dirname "$0")/../ui"
streamlit run streamlit_app.py

