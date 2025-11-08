#!/bin/bash
# Start ngrok tunnel for VerityNgn API
# This allows remote access from Streamlit Community Cloud or Google Colab

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚇 Starting ngrok tunnel for VerityNgn API${NC}"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}❌ ngrok is not installed${NC}"
    echo ""
    echo "Install ngrok:"
    echo "  macOS:   brew install ngrok"
    echo "  Linux:   snap install ngrok"
    echo "  Windows: choco install ngrok"
    echo ""
    echo "Or download from: https://ngrok.com/download"
    exit 1
fi

# Check if API is running
if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  API is not running on port 8080${NC}"
    echo ""
    echo "Start the API first:"
    echo "  docker compose up api"
    echo "  OR"
    echo "  python -m verityngn.api"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ API is running on port 8080${NC}"
echo ""

# Start ngrok
echo -e "${GREEN}🚀 Starting ngrok tunnel...${NC}"
echo ""
echo "This will create a public URL that tunnels to your local API."
echo "You can use this URL in:"
echo "  - Streamlit Community Cloud"
echo "  - Google Colab notebooks"
echo "  - Remote testing"
echo ""
echo -e "${YELLOW}⚠️  WARNING: This exposes your local API to the internet!${NC}"
echo "   Only use this for testing, and stop the tunnel when done."
echo ""

# Check if authtoken is configured
if ! ngrok config check &> /dev/null; then
    echo -e "${YELLOW}⚠️  ngrok authtoken not configured${NC}"
    echo ""
    echo "Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "Then run: ngrok authtoken YOUR_TOKEN"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start ngrok tunnel
echo -e "${GREEN}📡 Starting tunnel on port 8080...${NC}"
echo ""
echo "Press Ctrl+C to stop the tunnel"
echo ""
echo "Once started, look for the 'Forwarding' line to get your public URL:"
echo "  Example: https://1234-56-78-90-12.ngrok-free.app -> http://localhost:8080"
echo ""

# Start ngrok with web interface on 4040
ngrok http 8080 --log=stdout



