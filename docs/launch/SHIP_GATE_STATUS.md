# Ship-gate pre-flight — 2026-10-25

**Branch:** `release/v3.0.0`  
**HEAD:** `94f62f6` (uncommitted platform-refresh files sit on this SHA)  
**Published tag `v3.0.0`:** moving off `c740bad` on operator go 2026-10-26

## Pre-flight (this pass)

| Check | Result |
|-------|--------|
| Open-core boundary scan | PASS |
| Unit: MCP + claim schema + CLI/boundary | PASS (7 tests) |
| Clean Python 3.12 venv `pip install -e .` | PASS — `verityngn 3.0.0`, CLI help |
| Release paper PDF | Present (`papers/verityngn_oss_v3_release.pdf`, 7 pages / 2.19MB) |
| Browser gallery / GitHub | PASS (see `BROWSER_VERIFY_v3.md`) |
| Streamlit demo | FAIL (asleep) — wake before launch blast |
| rfkit extract tests | PASS (69) at `~/proj/rfkit-oss` |

## Operator go (2026-10-26)

1. Retag `v3.0.0` to this branch tip (includes platform pack)  
2. Fast-forward `origin/main` to `release/v3.0.0` (do **not** use local `main` commit `68703d7`, which has `.downloads` media)  
3. Publish `verityngn==3.0.0` to PyPI  
4. GitHub release assets  
5. Public `gh repo create` for rfkit still waits on Derrick `OPEN_CLOSED.md`

See [`SHIP_CLICKS_v3.md`](SHIP_CLICKS_v3.md).
