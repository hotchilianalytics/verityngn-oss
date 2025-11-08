#!/bin/bash
# Quick authentication script for VerityNgn

echo "🔐 VerityNgn Authentication Setup"
echo "================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found!"
    echo ""
    echo "Please install Google Cloud SDK:"
    echo "https://cloud.google.com/sdk/docs/install"
    echo ""
    exit 1
fi

# Check current auth status
echo "Checking current authentication status..."
if gcloud auth application-default print-access-token &> /dev/null; then
    echo "✅ Already authenticated!"
    echo ""
    echo "Your credentials are valid. You can run:"
    echo "  cd ui"
    echo "  streamlit run streamlit_app.py"
    echo ""
    exit 0
fi

# Need to authenticate
echo "⚠️  Not authenticated yet."
echo ""
echo "This will:"
echo "  1. Open your browser"
echo "  2. Ask you to log in to Google"
echo "  3. Grant access to your Google Cloud project"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Run authentication
echo ""
echo "Opening browser for authentication..."
gcloud auth application-default login

# Check if it succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Authentication successful!"
    echo ""
    echo "You can now run VerityNgn:"
    echo "  cd ui"
    echo "  streamlit run streamlit_app.py"
    echo ""
else
    echo ""
    echo "❌ Authentication failed"
    echo ""
    echo "Try running manually:"
    echo "  gcloud auth application-default login"
    echo ""
    exit 1
fi










