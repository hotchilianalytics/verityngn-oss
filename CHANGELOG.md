# Changelog

All notable changes to VerityNgn will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-11-12

### Added
- **Workflow Logging System**: Comprehensive debug-level logging saved to `.log` files in outputs directory
- **Streamlit Community Cloud Deployment**: API-first architecture enabling cloud-hosted UI
- **Migration Script**: Automated script for file restructuring (`scripts/migrate_to_milestone.sh`)
- **Test Directory Structure**: Organized test files into `test/{unit,integration,debug,scripts,utils}/`
- **Documentation Organization**: Moved development notes to `docs/cursor_dev/` and deployment guides to `docs/deployment/`

### Changed
- **File Structure**: Major reorganization of test files and documentation
  - Test files moved from root to `test/` directory
  - Development notes moved to `docs/cursor_dev/`
  - Deployment guides moved to `docs/deployment/`
- **API Polling**: Reduced polling frequency from 2s to 5-15s with exponential backoff
- **Error Handling**: Enhanced permission error handling for cloud environments
- **Gallery Component**: Added default values for missing fields to prevent KeyErrors

### Fixed
- **Gallery KeyError**: Fixed missing `youtube_url` and `submitted_at` field errors
- **Permission Errors**: Fixed Streamlit Cloud filesystem permission issues
- **Excessive Polling**: Reduced API load by 60-75% through exponential backoff

### Security
- Enhanced error handling prevents information leakage in cloud environments

## [2.0.0] - 2025-10-28

### Added
- Intelligent video segmentation (86% reduction in API calls)
- Enhanced multi-pass claim extraction with specificity scoring
- Absence claim generation
- Refined counter-intelligence weighting

### Changed
- Processing speed: 6-7x faster for typical videos
- Context window utilization: 3% → 58% (19x improvement)

---

## Migration Guide

### For Users Upgrading to v2.1.0

**Test Files:**
- Old location: `test_*.py` in root directory
- New location: `test/{unit,integration,debug}/*.py`
- **Action**: Update any scripts that reference test files

**Documentation:**
- Development notes: Now in `docs/cursor_dev/`
- Deployment guides: Now in `docs/deployment/`
- **Action**: Update bookmarks and links

**No Breaking Changes:**
- API endpoints remain unchanged
- Report formats remain unchanged
- Configuration files remain unchanged

