#!/bin/bash
# Quick test runner for tLJC8hkK-ao video
# Usage: ./run_test_tl.sh

set -e

cd "$(dirname "$0")"

echo "🔬 VerityNgn Test Runner - LIPOZEM Video"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Please create .env file with your credentials"
    echo "   See env.example for template"
    exit 1
fi

# Load .env and export GOOGLE_APPLICATION_CREDENTIALS if set
if grep -q "GOOGLE_APPLICATION_CREDENTIALS=" .env; then
    export $(grep "GOOGLE_APPLICATION_CREDENTIALS=" .env | xargs)
    echo "✅ Loaded GOOGLE_APPLICATION_CREDENTIALS from .env"
else
    echo "⚠️  Warning: GOOGLE_APPLICATION_CREDENTIALS not found in .env"
fi

# Check if service account file exists
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ] && [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "✅ Service account file found: $GOOGLE_APPLICATION_CREDENTIALS"
else
    echo "⚠️  Warning: Service account file not found or not configured"
fi

echo ""
echo "🚀 Starting test..."
echo ""

# Run test
python test_tl_video.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ Test completed successfully!"
    echo ""
    echo "📂 View results:"
    echo "   HTML: verityngn/outputs/tLJC8hkK-ao/*/tLJC8hkK-ao_report.html"
    echo "   JSON: verityngn/outputs/tLJC8hkK-ao/*/tLJC8hkK-ao_report.json"
else
    echo ""
    echo "❌ Test failed with exit code: $exit_code"
    exit $exit_code
fi



















