#!/bin/bash
# Run test with progress logging enabled

cd "$(dirname "$0")"

echo "🚀 VerityNgn Test with Progress Logging"
echo "========================================"
echo ""
echo "✅ Progress logging: ENABLED"
echo "✅ Segment duration: 300 seconds (5 minutes)"
echo "✅ Expected segments: 7 for 33-minute video"
echo ""
echo "You will see progress updates every 8-12 minutes."
echo "Total expected time: 56-84 minutes"
echo ""
echo "Starting test..."
echo ""

# Load environment variables from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Ensure critical variables are set
if [ -z "$GOOGLE_CLOUD_PROJECT" ] && [ -z "$PROJECT_ID" ]; then
    echo "⚠️  Adding GOOGLE_CLOUD_PROJECT to environment..."
    export GOOGLE_CLOUD_PROJECT="verityindex-0-0-1"
    export PROJECT_ID="verityindex-0-0-1"
fi

if [ -z "$LOCATION" ]; then
    export LOCATION="us-central1"
fi

# Run test
python test_tl_video.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ Test completed successfully!"
    echo ""
    echo "📂 View results:"
    latest_dir=$(ls -td verityngn/outputs/tLJC8hkK-ao/*/tLJC8hkK-ao_report.html 2>/dev/null | head -1)
    if [ -n "$latest_dir" ]; then
        echo "   $latest_dir"
    fi
else
    echo ""
    echo "❌ Test failed with exit code: $exit_code"
fi

exit $exit_code

