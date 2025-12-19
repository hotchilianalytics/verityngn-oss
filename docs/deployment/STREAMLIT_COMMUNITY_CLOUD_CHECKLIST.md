# Streamlit Community Cloud Release Checklist (VerityNgn UI)

## Secrets contract (minimum)

- **Required**: `CLOUDRUN_API_URL`
  - Example:

```toml
CLOUDRUN_API_URL = "https://your-cloudrun-service.run.app"
```

## Pre-deploy

- [ ] `main` is green in CI (smoke + secret scan)
- [ ] Cloud Run API is deployed (and points at the expected revision)
- [ ] Gallery endpoint works (videos list and report links load)

## Deploy (Streamlit Cloud UI)

- [ ] Main file path set to `ui/streamlit_app.py`
- [ ] Secrets set (at least `CLOUDRUN_API_URL`)
- [ ] App boots without errors

## Post-deploy sanity checks

- [ ] **Verify Video** tab loads
- [ ] **🖼️ Open Gallery** buttons navigate correctly
- [ ] **Backend mode** defaults to **Cloud Run** when `CLOUDRUN_API_URL` is present
- [ ] **Processing** tab health check passes in Cloud Run mode
- [ ] **Gallery** tab loads and “View Report” works
- [ ] Channel selector works without `YOUTUBE_API_KEY` (yt-dlp fallback)

## Public-safe guardrails (expected behavior)

- **Rate limit**: best-effort per-session limit (default: 3 verifications/hour)
  - Override with `VERITYNGN_UI_RATE_LIMIT_PER_HOUR`
- **Video duration cap**: best-effort client-side check (default: 60 minutes)
  - Override with `VERITYNGN_UI_MAX_VIDEO_SECONDS`
- **Max claims cap**: public default/cap (default cap: 25)
  - Override with `VERITYNGN_UI_MAX_CLAIMS_MAX` / `VERITYNGN_UI_MAX_CLAIMS_DEFAULT`
- **Submission history**: opt-in toggle (“Remember my submissions (this session)”)


