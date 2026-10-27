# rfkit OSS extract — Phase 1 status

**Date:** 2026-10-25  
**Tree:** `~/proj/rfkit-oss` (Apache-2.0, fresh-history *intent*)  
**Tests:** 69 passed (`unittest` via the private rfkit venv; system Python lacks PyYAML)

## What is in the extract

Matcher (`_typed_incident_score` / `junior_obvious`), EDGAR adapters, ontologies, `specimen` / `review` CLI, committee / coverage / C-suite renderers, shorts adapter (allegation + conflict banner; GOF refused as a 10-K demo).

## What is not

Vault, incident-log ingest, counsel-brief packaging, outreach CRM, `derrick_reply_*`, NDA / engagement drafts, prices, GOF job files.

## Derrick review (gate before GitHub)

[`~/proj/rfkit-oss/OPEN_CLOSED.md`](file:///Users/ajjc/proj/rfkit-oss/OPEN_CLOSED.md) is the open/closed split plus public-example ask (Microsoft, UnitedHealth). **Do not `gh repo create` until that review lands.**

## Git init (operator)

Auto-review blocked `git init` outside this workspace. After Derrick signs the split:

```bash
bash scripts/init_rfkit_oss_git.sh
# then, only when asked:
#   gh repo create hotchilianalytics/rfkit --public --source ~/proj/rfkit-oss --push
```

## Pin from VerityNgn

```bash
pip install -e ../rfkit-oss
pip install -e '.[disclosure]'
```

`verityngn[disclosure]` is an extra marker today (empty deps) until the public package is on PyPI. Shared JSON: `verityngn.schemas.claim_risk`.
