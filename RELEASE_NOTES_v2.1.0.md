# VerityNgn v2.1.0 Release Notes

**Release Date**: November 12, 2025  
**Milestone**: Streamlit Cloud Deployment & Workflow Logging

---

## 🎉 What's New

### Workflow Logging System
Comprehensive debug-level logging is now saved to `.log` files alongside reports in the outputs directory. This enables detailed debugging and workflow analysis.

**Location**: `outputs/{video_id}/{video_id}_workflow.log`

**Features**:
- DEBUG-level logging with function names and line numbers
- Complete workflow trace from start to finish
- API call details and responses
- Error traces with full stack traces
- Performance metrics

### Streamlit Community Cloud Deployment
The UI can now be deployed to Streamlit Community Cloud with an API-first architecture.

**Features**:
- Cloud-hosted Streamlit UI
- Public API access via ngrok tunneling
- API mode detection for cloud environments
- Enhanced error handling for sandboxed filesystems

### Reduced API Polling
Status polling now uses exponential backoff (5-15s intervals) instead of fixed 2s intervals, reducing API load by 60-75%.

### Enhanced Error Handling
- Gallery component handles missing fields gracefully
- Permission errors handled for cloud environments
- API mode detection for automatic configuration

---

## 📦 File Structure Changes

### Test Files
**Old**: `test_*.py` in root directory  
**New**: `test/{unit,integration,debug,scripts,utils}/`

### Documentation
**Old**: Mixed markdown files in root  
**New**: 
- Development notes → `docs/cursor_dev/`
- Deployment guides → `docs/deployment/`

---

## 🔧 Technical Improvements

### Container Optimization
- Multi-stage Docker builds with Conda
- Reduced image sizes by ~40%
- Faster builds with dependency caching

### Code Organization
- 87 files reorganized
- Better separation of concerns
- Improved maintainability

---

## 🐛 Bug Fixes

- Fixed Gallery KeyError for missing `youtube_url` field
- Fixed Streamlit Cloud permission errors
- Fixed excessive API polling

---

## 📚 Documentation Updates

- Updated research paper with v2.1.0 features
- Added deployment architecture section
- Created CHANGELOG.md
- Created migration guide

---

## ⚠️ Breaking Changes

**File Locations:**
- Test files moved to `test/` directory
- Documentation files moved to `docs/` subdirectories

**Migration:**
- Update any scripts referencing test files
- Update documentation links
- See `MIGRATION_GUIDE.md` for details

---

## 🚀 Upgrade Instructions

1. Pull latest code: `git pull origin main`
2. Rebuild containers: `./scripts/rebuild_all_containers.sh`
3. Update any custom scripts referencing moved files
4. Review `CHANGELOG.md` for details

---

## 📊 Statistics

- **Files Moved**: 87 files
- **Test Files**: 16 files reorganized
- **Documentation**: ~55 files reorganized
- **API Load Reduction**: 60-75%
- **Image Size Reduction**: ~40%

---

## 🙏 Acknowledgments

Thanks to all contributors and users who provided feedback during the development of v2.1.0.

---

**Full Changelog**: See [CHANGELOG.md](CHANGELOG.md)

