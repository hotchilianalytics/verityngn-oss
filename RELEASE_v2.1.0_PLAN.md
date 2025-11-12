# 🎯 Milestone Release v2.1.0 - Final Plan

**Date**: November 12, 2025  
**Milestone**: v2.1.0 - Streamlit Cloud Deployment & Workflow Logging  
**Status**: Ready for Execution

---

## 📋 Quick Summary

This milestone release includes:
1. ✅ Streamlit Community Cloud deployment
2. ✅ Workflow logging system (.log files)
3. ✅ Enhanced error handling (Gallery, permissions)
4. ✅ Reduced API polling (exponential backoff)
5. 📦 Code organization (test/ and docs/ restructuring)
6. 📄 Updated research papers

---

## ✅ Pre-Execution Checklist

### 1. Code Commit & Push
- [x] All fixes committed (gallery, polling, logging)
- [ ] Commit any remaining uncommitted changes
- [ ] Push to remote
- [ ] Verify push succeeded

### 2. Backup & Tagging
- [ ] Create backup branch: `git checkout -b milestone-v2.1.0-backup`
- [ ] Create pre-restructure tag: `git tag v2.0.9-pre-restructure`
- [ ] Push tags: `git push --tags`

### 3. Verification
- [ ] Run all tests: `python test_*.py`
- [ ] Verify Docker builds: `docker compose build --no-cache api`
- [ ] Check current file structure

---

## 🚀 Execution Steps

### Phase 1: Commit Current Code (10 min)
```bash
git add -A
git commit -m "Milestone v2.1.0: Streamlit Cloud deployment, workflow logging, and error fixes"
git push origin main
```

### Phase 2: File Restructuring (2-3 hours)

#### 2.1 Test Files (45 min)
```bash
# Create structure
mkdir -p test/{unit,integration,debug,scripts,utils}

# Move files (using git mv to preserve history)
git mv test_imports.py test/unit/
git mv test_credentials.py test/unit/
git mv test_claim_quality.py test/unit/
git mv test_ngrok.py test/unit/

git mv test_tl_video.py test/integration/
git mv test_enhanced_claims.py test/integration/
git mv test_deep_ci_integration.py test/integration/
git mv test_verification_json_fix.py test/integration/
git mv test_extraction.py test/integration/

git mv test_tl_video_debug.py test/debug/
git mv test_hang_fix.py test/debug/
git mv test_sherlock_timeout_fix.py test/debug/

git mv run_test_tl.sh test/scripts/
git mv run_test_with_credentials.sh test/scripts/
git mv RUN_TEST_WITH_PROGRESS.sh test/scripts/

git mv verityngn/utils/test_generate_report.py test/utils/

# Update imports in test files
# (Manual step - update sys.path.insert() calls)
```

#### 2.2 Documentation Files (60 min)
```bash
# Create directories
mkdir -p docs/cursor_dev docs/deployment

# Move development notes
git mv SHERLOCK_*.md docs/cursor_dev/ 2>/dev/null || true
git mv CHECKPOINT_*.md docs/cursor_dev/ 2>/dev/null || true
git mv *_FIX*.md docs/cursor_dev/ 2>/dev/null || true
git mv *_COMPLETE.md docs/cursor_dev/ 2>/dev/null || true
git mv *_SUMMARY.md docs/cursor_dev/ 2>/dev/null || true

# Move deployment guides
git mv DEPLOY_*.md docs/deployment/ 2>/dev/null || true
git mv DEPLOYMENT_*.md docs/deployment/ 2>/dev/null || true
git mv STREAMLIT_*.md docs/deployment/ 2>/dev/null || true
git mv NGROK_*.md docs/deployment/ 2>/dev/null || true
```

### Phase 3: Papers Update (45 min)
- [ ] Review `papers/verityngn_research_paper.md`
- [ ] Add Section 8: Workflow Logging System
- [ ] Update Section 9: Deployment Architecture (Streamlit Cloud)
- [ ] Add error handling improvements
- [ ] Generate updated PDF

### Phase 4: Script Verification (15 min)
- [x] `rebuild_all_containers.sh` already uses `--no-cache` ✅
- [ ] Check other build scripts
- [ ] Update script paths if needed

### Phase 5: Release Documentation (30 min)
- [ ] Create `CHANGELOG.md`
- [ ] Create `RELEASE_NOTES_v2.1.0.md`
- [ ] Update `README.md` with new structure
- [ ] Create `MIGRATION_GUIDE.md`

### Phase 6: Final Verification (30 min)
- [ ] Run all tests
- [ ] Verify Docker builds
- [ ] Check documentation links
- [ ] Create git tag: `git tag v2.1.0`
- [ ] Push tag: `git push --tags`

---

## 🔍 Sherlock Analysis Summary

### Critical Risks Identified:
1. **Import Path Breaking** (HIGH) - All test files need import updates
2. **Documentation Links** (MEDIUM) - Many markdown links will break
3. **Script Dependencies** (MEDIUM) - Shell scripts reference moved files

### Mitigations:
1. ✅ Use `git mv` to preserve history
2. ✅ Incremental migration with testing
3. ✅ Create symlinks for backward compatibility
4. ✅ Update imports immediately after moves
5. ✅ Create verification script

### Improvements Added:
1. ✅ Migration script created (`scripts/migrate_to_milestone.sh`)
2. ✅ Backup branch strategy
3. ✅ Version tagging before/after
4. ✅ Incremental phase approach
5. ✅ Comprehensive risk assessment

---

## 📊 File Count Summary

**Test Files to Move:**
- Unit tests: 4 files
- Integration tests: 5 files
- Debug tests: 3 files
- Test scripts: 3 files
- Utils test: 1 file
- **Total: 16 files**

**Documentation Files to Move:**
- Development notes: ~40 files
- Deployment guides: ~15 files
- **Total: ~55 files**

**Total Files to Move: ~71 files**

---

## ⚠️ Breaking Changes

1. **Test File Locations**
   - Old: `test_*.py` in root
   - New: `test/{unit,integration,debug}/*.py`
   - **Impact**: Scripts and docs referencing tests will break

2. **Documentation Locations**
   - Old: `*.md` files in root
   - New: `docs/cursor_dev/` and `docs/deployment/`
   - **Impact**: Links in README and other docs will break

**Mitigation**: Create symlinks for 3-6 months, then remove

---

## ✅ Success Criteria

- [ ] All code committed and pushed
- [ ] Backup branch and tags created
- [ ] Test files organized in `test/` directory
- [ ] Documentation organized in `docs/` structure
- [ ] Papers updated with latest features
- [ ] All tests pass
- [ ] Docker builds succeed
- [ ] Documentation links work
- [ ] Release notes created
- [ ] Git tag v2.1.0 created and pushed

---

## 📝 Next Steps

1. Review this plan
2. Execute Phase 1 (commit & push)
3. Create backup branch and tags
4. Execute migration script in dry-run mode
5. Review dry-run results
6. Execute migration
7. Update imports and links
8. Verify everything works
9. Create release tag

---

**Ready to proceed?** Start with Phase 1: Code Commit & Push

