# Ship-gate — Monday 9 Nov 2026

**Branch:** `release/v3.0.0` (= `main` after Monday push)  
**Tag:** `v3.0.0` → Monday tip (examples + SB1507 public + deck)  
**Previous published tip:** `644e5b4`

## Pre-flight (this pass)

| Check | Result |
|-------|--------|
| Open-core boundary scan | PASS |
| Unit: MCP + claim schema | PASS (3) |
| SB1507 scorecard from dense checkpoint | PASS — 40 claims; §6.1=16; quant→inference 88.9%; `all_green` |
| Examples page | [`EXAMPLES.md`](EXAMPLES.md) — Lipozem · SB1507 · Nadella |
| SB1507 public copy | Chris approved; mp4 **not** in git |
| Example deck PDF | `docs/launch/decks/VerityNgn_3_Release_with_examples.pdf` (22 pages) |
| Streamlit demo | Operator click — wake https://verityngn.streamlit.app before blast |
| rfkit GitHub | Still waits on Derrick `OPEN_CLOSED.md` |
| SplitRisk | Separate sleeve / possible later company — **not** in this wheel |

## verityindex / commercial pin

| Item | Value |
|------|-------|
| Live commercial OSS pin (docs) | `94f62f6` — `~/proj/commercial/verityngn-backend-commercial/docs/OSS_V3_ENGINE_PIN.md` |
| Monday OSS tip | tip of `v3.0.0` after this push |
| Action | Bump Batch / Cloud Run pin `94f62f6` → Monday SHA; redeploy only if `gcloud` is already authed |

## PyPI

Wheels at `dist/verityngn-3.0.0-*.whl` / `.tar.gz`. Upload only when `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=pypi-…` are set:

```bash
python -m twine upload dist/verityngn-3.0.0-py3-none-any.whl dist/verityngn-3.0.0.tar.gz
```

Token: https://pypi.org/manage/account/token/ (Entire account scope for first publish).

## See also

[`SHIP_CLICKS_v3.md`](SHIP_CLICKS_v3.md) · [`EXAMPLES.md`](EXAMPLES.md) · [`BROWSER_VERIFY_v3.md`](BROWSER_VERIFY_v3.md)
