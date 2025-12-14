# Commercial MVP Decision Doc (Replit-first)

## Goal

Ship a paid version focused on users who need **multiple multimodal truthfulness reports** (batching, history, exports), while keeping OSS usable and safe.

## Recommended stack

### Auth
- **Clerk** (simple hosted auth, good Next.js ergonomics, teams/orgs)

### Billing
- **Stripe Billing** (subscriptions + metering-ready)
  - Start with fixed tiers, add metered overage later.

### App / Hosting
- **Replit** for speed to MVP.
- Keep the backend API boundary similar to the Cloud Run API to reduce future migration pain.

## Product scope (MVP)

### Must-have
- **Login**
- **Subscription gating** (free trial optional)
- **Submit single + batch**
- **Job tracking** (queued/running/completed/failed)
- **Report history** (per user/org)
- **Export** (HTML + JSON at minimum)
- **Usage meter** (reports/month; optionally minutes processed)

### Nice-to-have
- Saved channel lists / “good channels”
- Team sharing + comments
- PDF export

## Entitlements (initial proposal)

Define limits server-side (don’t trust the client):

- **Starter**:
  - 20 reports/month
  - 1 concurrent job
  - max video length: 20 minutes
- **Pro**:
  - 100 reports/month
  - 3 concurrent jobs
  - max video length: 45 minutes
- **Team**:
  - 300 reports/month (pooled)
  - 10 concurrent jobs
  - max video length: 60 minutes

## Architecture (minimal)

### Services
- **Web app** (Replit): UI + auth session
- **API**: submit jobs, status, list history, fetch reports
- **Worker**: run verifications and write outputs
- **Storage**:
  - Reports: object storage (S3/GCS)
  - Metadata: Postgres (jobs, users, entitlements, pointers to report blobs)

### Data model (sketch)
- `users` / `orgs`
- `subscriptions` (stripe customer + plan + status)
- `jobs` (video_url, channel_url optional, status, timestamps, cost estimate)
- `reports` (job_id, storage_url, summary fields, created_at)

## Milestones

1. **Week 1**: Auth + Stripe checkout + gated UI shell
2. **Week 2**: Submit job + worker + job status polling
3. **Week 3**: Report storage + history list + export
4. **Week 4**: Usage metering + admin tooling + launch

## Risks / mitigations

- **Cost blowups**: strict server-side limits + queues + per-plan caps.
- **Abuse**: rate limits, duration caps, concurrency limits, audit logs.
- **Privacy**: default private reports; explicit sharing controls.


