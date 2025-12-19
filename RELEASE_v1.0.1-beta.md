# Release v1.0.1-beta - Public Streamlit Hardening + Gallery Navigation

**Release Date:** 2025-12-14  
**Status:** Beta Release

## Highlights

- **Gallery-first report UX**: “Open Gallery / View in Gallery” buttons across Verify/Processing/Reports, with working navigation.
- **Public-safe defaults**:
  - Best-effort **session rate limiting** (default: 3 verifications/hour)
  - Best-effort **video duration cap** (default: 60 minutes)
  - Lower **max-claims** defaults/caps for cost control
  - **Submission history is opt-in** (privacy)
- **Debug hardening**: stack traces + Sherlock diagnostics are behind an explicit debug toggle.
- **CI added**: smoke checks + lightweight secret scan to prevent credential leaks.

## User-facing changes

### Navigation / Reports
- Reports are treated as living in **🖼️ Gallery**.
- “Recent Verifications” now links to Gallery (no broken page switch).
- Gallery search can be pre-filled with a `video_id` when you jump from another tab.

### Channel selector reliability
- If `YOUTUBE_API_KEY` is not configured, channel listing falls back to **yt-dlp** (best-effort).

## Developer / Ops changes

### CI
- Added GitHub Actions workflow: `.github/workflows/ci.yml`
  - UI compile smoke
  - Core compile + import smoke
  - Regex-based secret scan

### Docs
- Added Streamlit Community Cloud checklist: `docs/deployment/STREAMLIT_COMMUNITY_CLOUD_CHECKLIST.md`
- Updated `STREAMLIT_CLOUD_DEPLOYMENT.md` to link to the checklist

## Configuration knobs (optional)

- `VERITYNGN_UI_RATE_LIMIT_PER_HOUR` (default: `3`)
- `VERITYNGN_UI_MAX_VIDEO_SECONDS` (default: `1800`)
- `VERITYNGN_UI_MAX_CLAIMS_MAX` (default: `25`)
- `VERITYNGN_UI_MAX_CLAIMS_DEFAULT` (default: `15`)
- `VERITYNGN_UI_DEBUG=1` (enable verbose console logging in local workflow mode)


