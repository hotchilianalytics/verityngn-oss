#!/bin/bash
# Monitor VerityNgn API logs in real-time
# Shows workflow processing without the noise

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          🔍 MONITORING VERITYNGN API LOGS                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Showing workflow logs (filtering out HTTP noise)..."
echo "Press Ctrl+C to stop"
echo ""
echo "─────────────────────────────────────────────────────────────"

# Follow API logs and filter for workflow messages
docker compose logs -f api 2>&1 | grep -E "verityngn|INFO|WARNING|ERROR|Starting|Processing|Claims|Report|Complete|Failed" | grep -v "GET /" | grep -v "POST /" | grep -v "health"











