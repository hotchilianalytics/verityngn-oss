# 🎯 Milestone Release Plan - VerityNgn OSS

**Date**: November 12, 2025  
**Status**: Planning Phase  
**Milestone**: v2.1.0 - Streamlit Cloud Deployment & Workflow Logging

---

## 📋 Release Checklist

### Phase 1: Code Commit & Push ✅
- [ ] Stage all uncommitted changes
- [ ] Review changes for sensitive data
- [ ] Commit with descriptive message
- [ ] Push to remote repository
- [ ] Verify push succeeded

### Phase 2: File Restructuring 🔄

#### 2.1 Test Files Organization
**Current State:**
- Test files scattered in root: `test_*.py` (13 files)
- Test scripts in root: `run_test_*.sh` (4 files)
- Some tests in `tests/` directory
- Some tests in `verityngn/utils/`

**Target Structure:**
```
test/
├── unit/
│   ├── test_imports.py
│   ├── test_credentials.py
│   └── test_claim_quality.py
├── integration/
│   ├── test_tl_video.py
│   ├── test_enhanced_claims.py
│   ├── test_deep_ci_integration.py
│   └── test_verification_json_fix.py
├── debug/
│   ├── test_tl_video_debug.py
│   ├── test_hang_fix.py
│   └── test_sherlock_timeout_fix.py
├── scripts/
│   ├── run_test_tl.sh
│   ├── run_test_with_credentials.sh
│   └── RUN_TEST_WITH_PROGRESS.sh
└── utils/
    └── test_generate_report.py (move from verityngn/utils/)
```

**Actions:**
- [ ] Create `test/` directory structure
- [ ] Move test files to appropriate subdirectories
- [ ] Update import paths in test files
- [ ] Update documentation references
- [ ] Test that all tests still run

#### 2.2 Documentation Files Organization
**Current State:**
- 95+ markdown files in root directory
- Mix of development notes, deployment guides, summaries
- Some docs in `docs/` but inconsistent

**Target Structure:**
```
docs/
├── cursor_dev/           # Development session notes
│   ├── SHERLOCK_*.md     # All Sherlock session files
│   ├── CHECKPOINT_*.md   # Checkpoint summaries
│   ├── FIXES_*.md        # Bug fix summaries
│   └── DEPLOYMENT_*.md   # Deployment notes
├── guides/               # User guides (already exists)
├── api/                  # API documentation (already exists)
├── development/          # Development docs (already exists)
└── tutorials/            # Tutorials (already exists)
```

**Categorization:**
- **Development Notes** → `docs/cursor_dev/`:
  - All `SHERLOCK_*.md` files
  - All `CHECKPOINT_*.md` files
  - All `*_FIX*.md` files
  - All `*_COMPLETE.md` files
  - All `*_SUMMARY.md` files
  
- **Deployment Guides** → `docs/deployment/`:
  - `DEPLOY_*.md`
  - `DEPLOYMENT_*.md`
  - `STREAMLIT_*.md`
  - `NGROK_*.md`
  
- **User Guides** → `docs/guides/`:
  - `QUICK_START_*.md`
  - `SETUP_*.md`
  - `TESTING_*.md`
  - `HOW_TO_*.md`

**Actions:**
- [ ] Create `docs/cursor_dev/` directory
- [ ] Create `docs/deployment/` directory
- [ ] Categorize and move markdown files
- [ ] Update README.md with new structure
- [ ] Update any hardcoded paths in scripts

### Phase 3: Papers Update 📄

**Current Papers:**
- `verityngn_research_paper.md` (main paper)
- `intelligent_segmentation.md`
- `counter_intelligence_methodology.md`
- `probability_model_foundations.md`

**Latest Features to Document:**
1. **Workflow Logging System**
   - Comprehensive .log file generation
   - Debug-level logging with function names/line numbers
   - Saved alongside reports in outputs directory

2. **Streamlit Community Cloud Deployment**
   - API-first architecture
   - ngrok integration for public API access
   - Permission error handling
   - Reduced polling frequency (exponential backoff)

3. **Enhanced Error Handling**
   - Gallery KeyError fixes
   - Filesystem permission handling
   - API mode detection

4. **Container Optimization**
   - Conda-based multi-stage builds
   - Minimal environment files
   - Reduced image sizes

**Actions:**
- [ ] Review main research paper
- [ ] Add workflow logging section
- [ ] Update deployment architecture section
- [ ] Add error handling improvements
- [ ] Update methodology with latest improvements
- [ ] Generate updated PDF

### Phase 4: Script Updates 🔧

**Current State:**
- `scripts/rebuild_all_containers.sh` already uses `--no-cache`
- Other scripts may need updates

**Actions:**
- [ ] Verify `rebuild_all_containers.sh` uses `--no-cache` ✅ (already does)
- [ ] Check other build scripts
- [ ] Update any scripts that reference moved files
- [ ] Add `--no-cache` flag to any missing build commands

### Phase 5: Release Documentation 📝

**Create:**
- [ ] `CHANGELOG.md` with milestone changes
- [ ] `RELEASE_NOTES_v2.1.0.md`
- [ ] Update `README.md` with new structure
- [ ] Create migration guide for file structure changes

---

## 🔍 Sherlock Analysis & Improvements

### Critical Issues Found:

1. **Import Path Breaking** ⚠️ HIGH RISK
   - Moving test files will break imports
   - **Impact**: All test files use `sys.path.insert(0, str(repo_root))`
   - **Fix**: Update all `sys.path.insert()` calls to new paths
   - **Fix**: Add `__init__.py` files to test directories
   - **Fix**: Update relative imports
   - **Fix**: Create `conftest.py` for pytest if using pytest
   - **Test**: Run each test after moving to verify imports

2. **Documentation References** ⚠️ MEDIUM RISK
   - Many scripts/docs reference files by absolute paths
   - **Impact**: Broken links in README, guides, and scripts
   - **Fix**: Use relative paths or environment variables
   - **Fix**: Update all documentation links
   - **Fix**: Create redirect/symlink for backward compatibility
   - **Test**: Verify all markdown links work

3. **CI/CD Pipeline** ⚠️ MEDIUM RISK
   - If CI exists, test paths may break
   - **Impact**: CI builds may fail
   - **Fix**: Update CI configuration (GitHub Actions, etc.)
   - **Fix**: Verify tests still run in CI
   - **Fix**: Update test discovery paths
   - **Test**: Run CI locally or check GitHub Actions

4. **Git History** ⚠️ LOW RISK (if done correctly)
   - Moving files loses git history if using `mv`
   - **Impact**: Loss of file history and blame information
   - **Fix**: Use `git mv` instead of `mv` (preserves history)
   - **Fix**: Preserve file history
   - **Fix**: Consider `git log --follow` for moved files
   - **Test**: Verify `git log` shows history after move

5. **Docker Build Context** ⚠️ LOW RISK
   - Moving files may affect Docker build
   - **Impact**: Docker builds may fail or miss files
   - **Fix**: Verify Dockerfile COPY commands
   - **Fix**: Update .dockerignore if needed
   - **Fix**: Test Docker build after moves
   - **Test**: Run `docker compose build --no-cache` after moves

6. **Script Dependencies** ⚠️ MEDIUM RISK
   - Shell scripts reference test files by path
   - **Impact**: Scripts like `run_test_tl.sh` may break
   - **Fix**: Update all script paths
   - **Fix**: Use environment variables for paths
   - **Test**: Run all scripts after moves

7. **Python Package Structure** ⚠️ LOW RISK
   - Some tests import from `verityngn.utils.test_*`
   - **Impact**: May need to update package structure
   - **Fix**: Move `verityngn/utils/test_generate_report.py` to test/
   - **Fix**: Update imports in that file
   - **Test**: Verify imports work

### Recommended Improvements:

1. **Incremental Migration** ✅ HIGH PRIORITY
   - Don't move everything at once
   - Move in phases, test after each phase
   - Keep backward compatibility where possible
   - **Phase 1**: Move test files, test imports
   - **Phase 2**: Move docs, test links
   - **Phase 3**: Update papers, verify
   - **Phase 4**: Final verification

2. **Symlinks for Backward Compatibility** 💡 RECOMMENDED
   - Create symlinks for critical files in root
   - Example: `test_tl_video.py` → `test/integration/test_tl_video.py`
   - Remove after users migrate (document timeline)
   - Add deprecation warnings in symlinked files
   - **Benefit**: Zero breaking changes for existing users

3. **Automated Testing** ✅ CRITICAL
   - Run full test suite before/after moves
   - Verify all imports work
   - Check documentation links
   - **Script**: Create `scripts/verify_migration.sh`
   - **Checks**: Imports, links, Docker build, tests

4. **Version Tagging** ✅ ESSENTIAL
   - Create git tag for milestone: `v2.1.0`
   - Tag BEFORE major restructuring: `v2.0.9-pre-restructure`
   - Tag AFTER restructuring: `v2.1.0`
   - Allows easy rollback if needed
   - **Commands**: 
     ```bash
     git tag v2.0.9-pre-restructure
     git tag v2.1.0
     ```

5. **Migration Script** 💡 RECOMMENDED
   - Create script to automate file moves
   - Update imports automatically using sed/awk
   - Generate migration report
   - **File**: `scripts/migrate_to_milestone.sh`
   - **Features**: Dry-run mode, rollback capability

6. **Backup Branch** ✅ ESSENTIAL
   - Create backup branch before starting
   - **Command**: `git checkout -b milestone-v2.1.0-backup`
   - Allows easy recovery if something breaks
   - Keep until milestone is stable

7. **Documentation Updates** ✅ CRITICAL
   - Update README.md with new structure
   - Create MIGRATION_GUIDE.md
   - Update all internal documentation links
   - Add "Where did X go?" section to README

8. **Changelog Creation** ✅ ESSENTIAL
   - Create/update CHANGELOG.md
   - Document all breaking changes
   - List new features
   - Include migration instructions

---

## 🚀 Execution Plan

### Step 1: Pre-Migration (45 min)
1. Create backup branch: `git checkout -b milestone-v2.1.0-backup`
2. Create pre-restructure tag: `git tag v2.0.9-pre-restructure`
3. Run full test suite: 
   - `python test_*.py` (run all test files)
   - `./run_test_tl.sh` (verify integration test)
   - Document any failures
4. Document current state: List all files to be moved
5. Create migration script: `scripts/migrate_to_milestone.sh`
6. Test migration script in dry-run mode

### Step 2: Code Commit (10 min)
1. Stage all changes: `git add -A`
2. Review: `git status`
3. Commit: `git commit -m "Milestone v2.1.0: Streamlit Cloud deployment & workflow logging"`
4. Push: `git push origin main`

### Step 3: Test Files Migration (45 min)
1. Create test directory structure
2. Move files using `git mv` (preserves history)
3. Update imports in test files
4. Update scripts that reference tests
5. Run tests to verify

### Step 4: Documentation Migration (60 min)
1. Create `docs/cursor_dev/` and `docs/deployment/`
2. Categorize markdown files
3. Move files using `git mv`
4. Update README.md
5. Update any hardcoded paths

### Step 5: Papers Update (45 min)
1. Review latest features
2. Update main research paper
3. Update methodology papers
4. Generate PDF
5. Commit changes

### Step 6: Script Verification (15 min)
1. Verify rebuild script
2. Check other build scripts
3. Update any broken references
4. Test rebuild process

### Step 7: Release Documentation (30 min)
1. Create CHANGELOG.md
2. Create RELEASE_NOTES_v2.1.0.md
3. Update README.md
4. Create migration guide

### Step 8: Final Verification (30 min)
1. Run full test suite
2. Verify Docker builds work
3. Check all documentation links
4. Test deployment process
5. Create git tag: `git tag v2.1.0`

**Total Estimated Time**: ~5-6 hours (with testing and verification)

### Additional Recommendations:

1. **Create Migration Script First** (1 hour)
   - Write `scripts/migrate_to_milestone.sh`
   - Include dry-run mode
   - Include rollback capability
   - Test on a small subset first

2. **Batch Commits** (Recommended)
   - Commit test file moves separately
   - Commit doc moves separately
   - Commit papers update separately
   - Makes rollback easier if needed

3. **Verification Checklist** (30 min)
   - [ ] All tests pass
   - [ ] Docker builds succeed
   - [ ] Documentation links work
   - [ ] Scripts still function
   - [ ] No broken imports
   - [ ] Git history preserved

---

## 📊 Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Import path breaks | High | High | Test after each move, update imports immediately |
| Documentation links break | Medium | Medium | Use relative paths, verify all links |
| CI/CD pipeline breaks | Low | High | Test CI before/after, update configs |
| Docker build breaks | Low | High | Test Docker build after moves |
| User confusion | Medium | Low | Clear migration guide, symlinks |

---

## ✅ Success Criteria

- [ ] All code committed and pushed
- [ ] Test files organized in `test/` directory
- [ ] Documentation organized in `docs/` structure
- [ ] Papers updated with latest features
- [ ] All tests pass
- [ ] Docker builds succeed
- [ ] Documentation links work
- [ ] Release notes created
- [ ] Git tag created

---

## 📝 Notes

- Consider creating a `MIGRATION_GUIDE.md` for users
- Keep `README.md` updated with new structure
- Consider deprecation warnings for old paths
- Document breaking changes in CHANGELOG

