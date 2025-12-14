# Commercial Replit MVP Build Plan

This is an implementation-oriented checklist for building the paid product on Replit.

## Repo layout (recommended)

Split commercial code from OSS:

- `verityngn-oss` (this repo): engine + Streamlit community UI + Cloud Run API reference
- `verityngn-pro` (new private repo): web app + billing + multi-tenant backend + workers

## Core features (MVP)

### 1) Auth (Clerk)
- [ ] Clerk project created
- [ ] Organizations enabled (optional but recommended)
- [ ] Server-side auth middleware (verify JWT / session)
- [ ] User/org tables (or sync from Clerk webhooks)

### 2) Billing (Stripe)
- [ ] Products + Prices configured (Starter/Pro/Team)
- [ ] Checkout page + customer portal
- [ ] Webhook handler (subscription created/updated/canceled)
- [ ] Entitlement resolver (plan → limits)

### 3) Job submission + tracking
- [ ] `POST /jobs` (single video URL; optional channel expansion)
- [ ] `GET /jobs/:id` status
- [ ] `GET /jobs` list (paged)
- [ ] Background worker queue (BullMQ/Redis, or Cloud Tasks)
- [ ] Concurrency control per org + per plan

### 4) Report storage + history
- [ ] Object storage bucket (S3/GCS)
- [ ] Signed URL proxy endpoint (or short-lived signed URLs)
- [ ] Report metadata table (job_id → storage keys + summary fields)
- [ ] History UI (filters, search, “open report”)

### 5) Usage metering + limits
- [ ] Define meter: reports/month (+ optional minutes processed)
- [ ] Increment usage when job completes (or starts)
- [ ] Enforce limits at submit time
- [ ] Optional overage plan (metered billing later)

## UI (Replit web app)

- [ ] Submit single video
- [ ] Submit batch (paste list / upload CSV)
- [ ] Jobs page (status, retry, cancel)
- [ ] Reports page (open/download HTML + JSON)

## Security / compliance minimums

- [ ] Per-user/org access control on all endpoints
- [ ] Audit log table (job submitted, report accessed)
- [ ] Secret management (Replit secrets; no env committed)
- [ ] Abuse controls (rate limit + duration cap + concurrency cap)

## Milestone tickets (copy/paste)

1. Auth middleware + user/org model
2. Stripe checkout + webhook + entitlement mapping
3. Jobs API + worker queue + persistence
4. Report storage + signed access + UI history
5. Usage metering + enforcement + admin dashboard


