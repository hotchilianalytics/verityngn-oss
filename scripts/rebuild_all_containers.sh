#!/bin/bash
# Complete rebuild of all Docker containers from scratch
# This ensures all code changes are properly incorporated

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║        🔨 REBUILDING ALL CONTAINERS FROM SCRATCH 🔨         ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Stop and remove all containers
echo -e "${YELLOW}📦 Step 1: Stopping and removing all containers...${NC}"
docker compose down
echo -e "${GREEN}✅ Containers stopped and removed${NC}"
echo ""

# Step 2: Remove old images
echo -e "${YELLOW}🗑️  Step 2: Removing old Docker images...${NC}"
docker rmi verityngn-api:latest verityngn-streamlit:latest verityngn-ui:latest 2>/dev/null || echo "Some images didn't exist (this is OK)"
echo -e "${GREEN}✅ Old images removed${NC}"
echo ""

# Step 3: Rebuild API (no cache)
echo -e "${YELLOW}🏗️  Step 3: Rebuilding API container (no cache)...${NC}"
echo -e "${BLUE}This will take several minutes...${NC}"
docker compose build --no-cache api
echo -e "${GREEN}✅ API container rebuilt${NC}"
echo ""

# Step 4: Rebuild UI (no cache)
echo -e "${YELLOW}🎨 Step 4: Rebuilding UI container (no cache)...${NC}"
echo -e "${BLUE}This will take a few minutes...${NC}"
docker compose build --no-cache ui
echo -e "${GREEN}✅ UI container rebuilt${NC}"
echo ""

# Step 5: Start all containers
echo -e "${YELLOW}🚀 Step 5: Starting all containers...${NC}"
docker compose up -d
echo -e "${GREEN}✅ Containers started${NC}"
echo ""

# Step 6: Wait for health checks
echo -e "${YELLOW}⏳ Step 6: Waiting for containers to be healthy (20 seconds)...${NC}"
sleep 20
echo ""

# Step 7: Show status
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ REBUILD COMPLETE!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}📊 Container Status:${NC}"
docker compose ps
echo ""

# Step 8: Show access URLs
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🌐 Access Your Services:${NC}"
echo ""
echo -e "  ${GREEN}Streamlit UI:${NC}  http://localhost:8501"
echo -e "  ${GREEN}API Backend:${NC}   http://localhost:8080"
echo -e "  ${GREEN}API Health:${NC}    http://localhost:8080/health"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Step 9: Test API health
echo -e "${YELLOW}🏥 Testing API health...${NC}"
sleep 2
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ API is healthy and responding${NC}"
else
    echo -e "${RED}⚠️  API health check failed - check logs:${NC}"
    echo -e "   ${BLUE}docker compose logs api${NC}"
fi
echo ""

# Step 10: Check UI logs for output directory
echo -e "${YELLOW}📂 Checking UI output directory detection...${NC}"
docker compose logs ui 2>&1 | grep -i "Found output" | tail -1 || echo "Waiting for UI to fully start..."
echo ""

echo -e "${GREEN}✅ All done! Open ${BLUE}http://localhost:8501${GREEN} in your browser${NC}"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}📝 Quick Commands:${NC}"
echo ""
echo -e "  View logs:        ${BLUE}docker compose logs -f${NC}"
echo -e "  View API logs:    ${BLUE}docker compose logs -f api${NC}"
echo -e "  View UI logs:     ${BLUE}docker compose logs -f ui${NC}"
echo -e "  Stop services:    ${BLUE}docker compose down${NC}"
echo -e "  Restart services: ${BLUE}docker compose restart${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"


