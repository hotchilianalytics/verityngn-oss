#!/bin/bash
# scripts/view_workflow_logs.sh
#
# View only workflow processing logs, filtering out HTTP access logs

set -e

echo "📝 Viewing VerityNgn workflow logs (filtered)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Filtering out:"
echo "  - HTTP access logs (GET/POST requests)"
echo "  - Health check requests"
echo ""
echo "Showing only:"
echo "  - Workflow processing logs"
echo "  - Errors and warnings"
echo "  - Application-level messages"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Follow logs and filter out HTTP access logs
docker compose logs api -f --tail 100 | \
    grep -v "GET /api/v1/verification/status" | \
    grep -v "GET /health" | \
    grep -v "POST /api/v1/verification/verify HTTP" | \
    grep -v "200 OK$"
