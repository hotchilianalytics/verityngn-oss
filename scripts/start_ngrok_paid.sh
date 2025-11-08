#!/bin/bash
# Start ngrok tunnel for VerityNgn API - PAID ACCOUNT VERSION
# This script uses your paid ngrok account features

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║          🚇 Starting ngrok Tunnel (PAID ACCOUNT) 🚇          ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}❌ ngrok is not installed${NC}"
    echo ""
    echo "Install ngrok:"
    echo -e "  ${YELLOW}macOS:${NC}   brew install ngrok"
    echo -e "  ${YELLOW}Linux:${NC}   snap install ngrok"
    echo -e "  ${YELLOW}Windows:${NC} choco install ngrok"
    echo ""
    echo "Or download from: https://ngrok.com/download"
    exit 1
fi

# Check if API is running
if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  API is not running on port 8080${NC}"
    echo ""
    echo "Start the API first:"
    echo -e "  ${GREEN}docker compose up api${NC}"
    echo -e "  ${YELLOW}OR${NC}"
    echo -e "  ${GREEN}python -m verityngn.api${NC}"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ API is healthy on port 8080${NC}"
echo ""

# Check ngrok configuration
echo -e "${BLUE}🔍 Checking ngrok configuration...${NC}"
if ! ngrok config check &> /dev/null; then
    echo -e "${RED}❌ ngrok configuration error${NC}"
    exit 1
fi
echo -e "${GREEN}✅ ngrok is configured (paid account detected)${NC}"
echo ""

# Determine which config to use
if [ -f ".ngrok.yml" ]; then
    CONFIG_FILE=".ngrok.yml"
    echo -e "${GREEN}✅ Using project ngrok config: .ngrok.yml${NC}"
    USE_PROJECT_CONFIG=true
else
    echo -e "${YELLOW}ℹ️  Using global ngrok config${NC}"
    USE_PROJECT_CONFIG=false
fi
echo ""

echo -e "${GREEN}🚀 Starting ngrok tunnel...${NC}"
echo ""
echo "This creates a public URL that tunnels to your local API."
echo ""
echo -e "${GREEN}✨ PAID ACCOUNT BENEFITS:${NC}"
echo "  ✓ Custom/reserved domains (if configured)"
echo "  ✓ Higher rate limits"
echo "  ✓ More simultaneous tunnels"
echo "  ✓ IP whitelisting"
echo "  ✓ Persistent URLs (don't change on restart)"
echo ""

# Show usage instructions
echo -e "${BLUE}📱 USAGE:${NC}"
echo "  - Streamlit Community Cloud"
echo "  - Google Colab notebooks"
echo "  - Remote API testing"
echo "  - Mobile app development"
echo ""

# Start ngrok with appropriate config
echo -e "${YELLOW}⚠️  Note: Your API will be publicly accessible!${NC}"
echo "   Use Ctrl+C to stop the tunnel when done."
echo ""
echo -e "${GREEN}📡 Starting tunnel on port 8080...${NC}"
echo ""

if [ "$USE_PROJECT_CONFIG" = true ]; then
    echo -e "${GREEN}🎯 Starting named tunnel 'verityngn-api'...${NC}"
    echo ""
    echo "Look for the 'Forwarding' line to get your public URL:"
    echo ""
    
    # Start ngrok using the named tunnel from config
    ngrok start verityngn-api --config="${CONFIG_FILE}" --log=stdout
else
    echo "Look for the 'Forwarding' line to get your public URL:"
    echo "  Example: https://your-domain.ngrok.io -> http://localhost:8080"
    echo ""
    
    # Start ngrok with basic HTTP tunnel (will use global config)
    ngrok http 8080 --log=stdout
fi

