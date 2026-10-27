# Ship-gate pre-flight — 2026-10-25

**Branch:** `release/v3.0.0`  
**HEAD / tag:** `644e5b4` (`v3.0.0`)  
**Previous tag:** `c740bad` (moved on operator go 2026-10-26)

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

| Step | Result |
|------|--------|
| Push `release/v3.0.0` | **Done** `644e5b4` |
| Fast-forward `origin/main` | **Done** `f28b3e8` → `644e5b4` (did not use local `68703d7`) |
| Retag `v3.0.0` | **Done** annotated tag `ca76d68` → `644e5b4` |
| GitHub release | **Done** https://github.com/hotchilianalytics/verityngn-oss/releases/tag/v3.0.0 |
| PyPI `verityngn==3.0.0` | **Blocked** — no `TWINE_PASSWORD` / PyPI API token in this environment |
| `gh repo create` rfkit | Still waits on Derrick `OPEN_CLOSED.md` |

Wheels are built at `dist/verityngn-3.0.0-*.whl` / `.tar.gz`. To finish PyPI:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-...   # API token
python -m twine upload dist/verityngn-3.0.0-py3-none-any.whl dist/verityngn-3.0.0.tar.gz
```

See [`SHIP_CLICKS_v3.md`](SHIP_CLICKS_v3.md).
