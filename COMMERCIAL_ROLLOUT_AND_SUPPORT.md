# Commercial Rollout + Support Plan

## Rollout phases

### Phase 0: Private alpha (5–10 users)
- [ ] Invite list + onboarding call script
- [ ] Shared feedback doc + weekly check-in
- [ ] Hard limits enabled (concurrency, duration, reports/month)

### Phase 1: Paid beta (self-serve)
- [ ] Pricing page + checkout + portal
- [ ] In-app onboarding (first job → first report → export)
- [ ] Status page + incident playbook

### Phase 2: Team plan
- [ ] Org/team management
- [ ] Shared report libraries + access controls
- [ ] Admin usage dashboard

## Customer support loop

- [ ] Support channel: email + in-app “Report a problem”
- [ ] Triage labels: billing / bug / model-quality / performance / feature
- [ ] SLA targets (beta): 48h response, 7d fix for P0/P1

## Telemetry (privacy-aware)

- [ ] Capture high-level events only (submit_job, job_complete, report_open)
- [ ] Avoid storing raw user content by default
- [ ] Provide “download diagnostics” for troubleshooting

## Migration story (OSS → paid)

- [ ] Document differences:
  - OSS: Streamlit UI + Cloud Run API
  - Paid: auth + billing + history + batch + guarantees
- [ ] “Import existing report” flow (optional)
- [ ] Clear data retention policy


