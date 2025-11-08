#!/bin/bash
# Quick test of local UI before deploying to Streamlit Community

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║          🧪 Testing VerityNgn UI Before Deployment 🧪        ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if UI is running in Docker
echo -e "${BLUE}1. Checking if UI is running...${NC}"
if docker compose ps ui | grep -q "Up"; then
    echo -e "${GREEN}✅ UI is running in Docker${NC}"
    echo -e "   Access at: ${GREEN}http://localhost:8501${NC}"
    UI_RUNNING=true
else
    echo -e "${YELLOW}⚠️  UI is not running in Docker${NC}"
    UI_RUNNING=false
fi
echo ""

# Check if API is running
echo -e "${BLUE}2. Checking if API is running...${NC}"
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API is healthy on port 8080${NC}"
    API_RUNNING=true
else
    echo -e "${YELLOW}⚠️  API is not running on port 8080${NC}"
    echo -e "   Start with: ${GREEN}docker compose up api${NC}"
    API_RUNNING=false
fi
echo ""

# Check ngrok
echo -e "${BLUE}3. Checking ngrok tunnel...${NC}"
if ps aux | grep -v grep | grep -q ngrok; then
    echo -e "${GREEN}✅ ngrok is running${NC}"
    echo -e "   Monitor at: ${GREEN}http://localhost:4040${NC}"
    NGROK_RUNNING=true
else
    echo -e "${YELLOW}⚠️  ngrok is not running${NC}"
    echo -e "   Start with: ${GREEN}ngrok http 8080${NC}"
    NGROK_RUNNING=false
fi
echo ""

# Check UI requirements
echo -e "${BLUE}4. Checking UI requirements...${NC}"
if [ -f "ui/requirements.txt" ]; then
    echo -e "${GREEN}✅ ui/requirements.txt exists${NC}"
    echo -e "   Dependencies:"
    cat ui/requirements.txt | grep -v "^#" | grep -v "^$" | sed 's/^/     /'
else
    echo -e "${RED}❌ ui/requirements.txt not found${NC}"
fi
echo ""

# Check streamlit config
echo -e "${BLUE}5. Checking Streamlit configuration...${NC}"
if [ -f "ui/.streamlit/config.toml" ]; then
    echo -e "${GREEN}✅ .streamlit/config.toml exists${NC}"
else
    echo -e "${YELLOW}⚠️  .streamlit/config.toml not found (optional)${NC}"
fi
echo ""

# Check for secrets example
echo -e "${BLUE}6. Checking secrets configuration...${NC}"
if [ -f "ui/.streamlit/secrets.toml.example" ]; then
    echo -e "${GREEN}✅ secrets.toml.example exists${NC}"
    echo ""
    echo -e "${YELLOW}📋 For Streamlit Community, add these secrets:${NC}"
    cat ui/.streamlit/secrets.toml.example | grep -v "^#" | sed 's/^/     /'
else
    echo -e "${YELLOW}⚠️  secrets.toml.example not found${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}📊 DEPLOYMENT READINESS SUMMARY${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ "$UI_RUNNING" = true ]; then
    echo -e "✅ Local UI: ${GREEN}READY${NC} - http://localhost:8501"
else
    echo -e "❌ Local UI: ${RED}NOT RUNNING${NC}"
    echo -e "   Run: ${YELLOW}docker compose up ui${NC}"
fi

if [ "$API_RUNNING" = true ]; then
    echo -e "✅ Local API: ${GREEN}READY${NC} - http://localhost:8080"
else
    echo -e "❌ Local API: ${RED}NOT RUNNING${NC}"
    echo -e "   Run: ${YELLOW}docker compose up api${NC}"
fi

if [ "$NGROK_RUNNING" = true ]; then
    echo -e "✅ ngrok: ${GREEN}RUNNING${NC} - http://localhost:4040"
else
    echo -e "❌ ngrok: ${RED}NOT RUNNING${NC}"
    echo -e "   Run: ${YELLOW}ngrok http 8080${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ "$UI_RUNNING" = true ] && [ "$API_RUNNING" = true ]; then
    echo -e "${GREEN}🎉 READY FOR DEPLOYMENT!${NC}"
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo -e "  1. Test UI locally: ${BLUE}http://localhost:8501${NC}"
    echo -e "  2. Push to GitHub: ${YELLOW}git push origin main${NC}"
    echo -e "  3. Deploy to Streamlit: ${BLUE}https://share.streamlit.io${NC}"
    echo -e "  4. Configure secrets with ngrok URL"
    echo ""
    echo -e "${BLUE}📚 See: DEPLOY_STREAMLIT_COMMUNITY.md for full guide${NC}"
else
    echo -e "${YELLOW}⚠️  NOT READY - Start missing services first${NC}"
    echo ""
    echo -e "${GREEN}Quick start all services:${NC}"
    echo -e "  ${YELLOW}docker compose up${NC}"
    echo -e "  ${YELLOW}ngrok http 8080${NC}  ${BLUE}(in another terminal)${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

