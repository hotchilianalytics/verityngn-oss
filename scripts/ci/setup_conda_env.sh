#!/bin/bash
# CI Helper Script: Setup Conda Environment
# Creates conda environment from environment-minimal.yml for CI and local testing
#
# Usage:
#   bash scripts/ci/setup_conda_env.sh
#
# This script:
#   1. Checks for conda/mamba installation
#   2. Creates conda environment from environment-minimal.yml
#   3. Activates the environment
#   4. Verifies installation

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/environment-minimal.yml"
ENV_NAME="verityngn"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║        🐍 Setting Up Conda Environment for CI 🐍           ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Error: environment-minimal.yml not found at: $ENV_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Environment file: $ENV_FILE${NC}"
echo ""

# Function to initialize conda
init_conda() {
    echo -e "${BLUE}1. Initializing conda...${NC}"
    
    # Try to find conda installation
    if [ -f "$(conda info --base)/etc/profile.d/conda.sh" ]; then
        source "$(conda info --base)/etc/profile.d/conda.sh"
        echo -e "${GREEN}✅ Conda initialized from conda.sh${NC}"
    elif command -v conda &> /dev/null; then
        eval "$(conda shell.bash hook)"
        echo -e "${GREEN}✅ Conda initialized from shell hook${NC}"
    else
        echo -e "${RED}❌ Error: conda not found. Please install miniconda or mambaforge.${NC}"
        echo -e "${YELLOW}   Download from: https://github.com/conda-forge/miniforge${NC}"
        exit 1
    fi
}

# Function to check for mamba (preferred) or use conda
check_mamba() {
    echo -e "${BLUE}2. Checking for mamba (faster than conda)...${NC}"
    
    if command -v mamba &> /dev/null; then
        echo -e "${GREEN}✅ Mamba found - will use mamba for faster dependency resolution${NC}"
        USE_MAMBA=true
    else
        echo -e "${YELLOW}⚠️  Mamba not found - will use conda (slower)${NC}"
        echo -e "${YELLOW}   Install mamba: conda install -n base -c conda-forge mamba${NC}"
        USE_MAMBA=false
    fi
    echo ""
}

# Function to create or update conda environment
create_env() {
    echo -e "${BLUE}3. Creating/updating conda environment: $ENV_NAME${NC}"
    
    # Check if environment already exists
    if conda env list | grep -q "^${ENV_NAME} "; then
        echo -e "${YELLOW}   Environment '$ENV_NAME' already exists - updating...${NC}"
        if [ "$USE_MAMBA" = true ]; then
            mamba env update -f "$ENV_FILE" --name "$ENV_NAME" --quiet
        else
            conda env update -f "$ENV_FILE" --name "$ENV_NAME" --quiet
        fi
        echo -e "${GREEN}✅ Environment updated${NC}"
    else
        echo -e "${BLUE}   Creating new environment...${NC}"
        if [ "$USE_MAMBA" = true ]; then
            mamba env create -f "$ENV_FILE" --quiet
        else
            conda env create -f "$ENV_FILE" --quiet
        fi
        echo -e "${GREEN}✅ Environment created${NC}"
    fi
    
    # Clean conda cache to save space
    if [ "$USE_MAMBA" = true ]; then
        mamba clean -afy
    else
        conda clean -afy
    fi
    echo ""
}

# Function to verify installation
verify_env() {
    echo -e "${BLUE}4. Verifying environment installation...${NC}"
    
    # Activate environment
    conda activate "$ENV_NAME"
    
    # Check Python version
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}   Python version: $PYTHON_VERSION${NC}"
    
    # Check key packages
    echo -e "${BLUE}   Checking key packages...${NC}"
    
    PACKAGES=("fastapi" "uvicorn" "pydantic" "yt-dlp" "ffmpeg")
    for pkg in "${PACKAGES[@]}"; do
        if python -c "import ${pkg//-/_}" 2>/dev/null || python -c "import ${pkg}" 2>/dev/null; then
            echo -e "${GREEN}   ✅ $pkg${NC}"
        else
            echo -e "${YELLOW}   ⚠️  $pkg (may not be importable, but installed)${NC}"
        fi
    done
    
    # Check ffmpeg binary
    if command -v ffmpeg &> /dev/null; then
        FFMPEG_VERSION=$(ffmpeg -version | head -n 1 | awk '{print $3}')
        echo -e "${GREEN}   ✅ ffmpeg: $FFMPEG_VERSION${NC}"
    else
        echo -e "${YELLOW}   ⚠️  ffmpeg binary not found in PATH${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Environment verification complete!${NC}"
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🎉 Conda environment '$ENV_NAME' is ready!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}To activate the environment manually:${NC}"
    echo -e "${YELLOW}   conda activate $ENV_NAME${NC}"
    echo ""
    echo -e "${BLUE}To run tests:${NC}"
    echo -e "${YELLOW}   conda activate $ENV_NAME${NC}"
    echo -e "${YELLOW}   python test/unit/test_imports.py${NC}"
    echo ""
}

# Main execution
main() {
    init_conda
    check_mamba
    create_env
    verify_env
}

# Run main function
main

