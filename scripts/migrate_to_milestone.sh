#!/bin/bash
# Migration script for Milestone v2.1.0 release
# Moves test files and documentation to new structure
#
# Usage:
#   ./scripts/migrate_to_milestone.sh --dry-run    # Preview changes
#   ./scripts/migrate_to_milestone.sh              # Execute migration
#   ./scripts/migrate_to_milestone.sh --rollback   # Rollback changes

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

DRY_RUN=false
ROLLBACK=false

# Parse arguments
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}🔍 DRY RUN MODE - No changes will be made${NC}"
elif [[ "$1" == "--rollback" ]]; then
    ROLLBACK=true
    echo -e "${RED}⏪ ROLLBACK MODE - Reverting changes${NC}"
fi

# Function to move file (preserves git history)
move_file() {
    local src=$1
    local dst=$2
    
    if [[ "$ROLLBACK" == true ]]; then
        # Rollback: move dst back to src
        if [[ -f "$dst" ]]; then
            echo -e "${YELLOW}Rolling back: $dst -> $src${NC}"
            if [[ "$DRY_RUN" != true ]]; then
                git mv "$dst" "$src" 2>/dev/null || mv "$dst" "$src"
            fi
        fi
    else
        # Normal: move src to dst
        if [[ -f "$src" ]]; then
            echo -e "${GREEN}Moving: $src -> $dst${NC}"
            if [[ "$DRY_RUN" != true ]]; then
                mkdir -p "$(dirname "$dst")"
                git mv "$src" "$dst" 2>/dev/null || mv "$src" "$dst"
            fi
        fi
    fi
}

# Function to update import paths in Python files
update_imports() {
    local file=$1
    local old_path=$2
    local new_path=$3
    
    if [[ "$ROLLBACK" == true ]]; then
        # Rollback: restore old paths
        if [[ -f "$file" ]]; then
            echo -e "${YELLOW}Restoring imports in: $file${NC}"
            if [[ "$DRY_RUN" != true ]]; then
                sed -i.bak "s|$new_path|$old_path|g" "$file"
                rm -f "${file}.bak"
            fi
        fi
    else
        # Normal: update to new paths
        if [[ -f "$file" ]]; then
            echo -e "${BLUE}Updating imports in: $file${NC}"
            if [[ "$DRY_RUN" != true ]]; then
                sed -i.bak "s|$old_path|$new_path|g" "$file"
                rm -f "${file}.bak"
            fi
        fi
    fi
}

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║        📦 MILESTONE v2.1.0 MIGRATION SCRIPT 📦               ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [[ "$ROLLBACK" != true ]]; then
    # Phase 1: Create directory structure
    echo -e "${YELLOW}📁 Phase 1: Creating directory structure...${NC}"
    if [[ "$DRY_RUN" != true ]]; then
        mkdir -p test/unit test/integration test/debug test/scripts
        mkdir -p docs/cursor_dev docs/deployment
    fi
    echo -e "${GREEN}✅ Directory structure created${NC}"
    echo ""
    
    # Phase 2: Move test files
    echo -e "${YELLOW}🧪 Phase 2: Moving test files...${NC}"
    
    # Unit tests
    move_file "test_imports.py" "test/unit/test_imports.py"
    move_file "test_credentials.py" "test/unit/test_credentials.py"
    move_file "test_claim_quality.py" "test/unit/test_claim_quality.py"
    move_file "test_ngrok.py" "test/unit/test_ngrok.py"
    
    # Integration tests
    move_file "test_tl_video.py" "test/integration/test_tl_video.py"
    move_file "test_enhanced_claims.py" "test/integration/test_enhanced_claims.py"
    move_file "test_deep_ci_integration.py" "test/integration/test_deep_ci_integration.py"
    move_file "test_verification_json_fix.py" "test/integration/test_verification_json_fix.py"
    move_file "test_extraction.py" "test/integration/test_extraction.py"
    
    # Debug tests
    move_file "test_tl_video_debug.py" "test/debug/test_tl_video_debug.py"
    move_file "test_hang_fix.py" "test/debug/test_hang_fix.py"
    move_file "test_sherlock_timeout_fix.py" "test/debug/test_sherlock_timeout_fix.py"
    
    # Test scripts
    move_file "run_test_tl.sh" "test/scripts/run_test_tl.sh"
    move_file "run_test_with_credentials.sh" "test/scripts/run_test_with_credentials.sh"
    move_file "RUN_TEST_WITH_PROGRESS.sh" "test/scripts/RUN_TEST_WITH_PROGRESS.sh"
    
    # Move utils test
    move_file "verityngn/utils/test_generate_report.py" "test/utils/test_generate_report.py"
    
    echo -e "${GREEN}✅ Test files moved${NC}"
    echo ""
    
    # Phase 3: Move documentation files
    echo -e "${YELLOW}📚 Phase 3: Moving documentation files...${NC}"
    
    # Development notes to cursor_dev
    for file in SHERLOCK_*.md CHECKPOINT_*.md *_FIX*.md *_COMPLETE.md *_SUMMARY.md; do
        if [[ -f "$file" ]]; then
            move_file "$file" "docs/cursor_dev/$file"
        fi
    done
    
    # Deployment guides
    for file in DEPLOY_*.md DEPLOYMENT_*.md STREAMLIT_*.md NGROK_*.md; do
        if [[ -f "$file" ]]; then
            move_file "$file" "docs/deployment/$file"
        fi
    done
    
    echo -e "${GREEN}✅ Documentation files moved${NC}"
    echo ""
    
    # Phase 4: Update imports in test files
    echo -e "${YELLOW}🔧 Phase 4: Updating imports...${NC}"
    # This would need to be customized based on actual import patterns
    echo -e "${BLUE}Note: Manual import updates may be needed${NC}"
    echo ""
    
    echo -e "${GREEN}✅ Migration complete!${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Next steps:${NC}"
    echo "  1. Review moved files"
    echo "  2. Update import paths in test files"
    echo "  3. Update documentation links"
    echo "  4. Run tests to verify"
    echo "  5. Commit changes"
else
    echo -e "${RED}Rollback functionality not fully implemented${NC}"
    echo -e "${YELLOW}Use git to restore: git checkout milestone-v2.1.0-backup${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

