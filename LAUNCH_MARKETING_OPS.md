# Launch Marketing Ops (OSS → Commercial)

This doc is a practical checklist for maximizing the open-source release, then converting interest into a commercial MVP.

## OSS launch (v1.0.1-beta)

### Release candidate (RC) freeze
- [ ] 24–48h freeze window for `main` (only bugfix PRs)
- [ ] Verify Streamlit app boots with **only** `CLOUDRUN_API_URL` set
- [ ] Verify Gallery navigation + report viewing works end-to-end
- [ ] CI green (smoke + secret scan)

### Demo assets (fast, high leverage)
- [ ] 60–120s screen-recording demo:
  - Paste a channel URL → pick video → Start → open Gallery → open report
- [ ] 2–3 “example reports” you can share publicly (safe content)
- [ ] 5–8 screenshots/gifs for README + GitHub Release page

### Distribution plan
- [ ] GitHub Release created for `v1.0.1-beta` using `RELEASE_v1.0.1-beta.md`
- [ ] Add “Getting Started” section in `README.md` pointing to Streamlit app + Cloud Run backend requirement
- [ ] Announcements:
  - [ ] Hacker News “Show HN” (include demo + clear limitations)
  - [ ] Product Hunt (optional) with the same demo assets
  - [ ] Twitter/LinkedIn (thread: problem → approach → demo → repo → roadmap)
  - [ ] Relevant communities (misinfo research, OSINT, ML engineering, Streamlit)

### Roadmap + contribution loop
- [ ] Create “Roadmap” GitHub issue(s) + label set (`good first issue`, `help wanted`)
- [ ] Create “Known limitations” issue(s) and link from README
- [ ] Add a short “How to contribute” pointer to `CONTRIBUTING.md`

### Post-launch ops
- [ ] Open a “Feedback thread” issue template or pinned issue
- [ ] Weekly triage cadence (label + close/repro)
- [ ] Write a short postmortem: what worked, what didn’t, next sprint focus

## Commercial follow-on (Replit MVP)

### Positioning
- Target user: teams/consultants doing **multiple** truthfulness reports per week.
- Primary value prop: faster, repeatable, multi-report workflow + history/export.

### MVP checklist (high-level)
- [ ] Auth + billing (Stripe + Clerk recommended)
- [ ] Entitlements (reports/month, concurrency, max video length)
- [ ] Report history + export (HTML/JSON/PDF)
- [ ] Usage metering + overage plan


