# VerityNgn 3.0.0 — runnable examples

Public copy-paste fixtures for the Monday 9 Nov 2026 release.  
**Tag:** `v3.0.0` on `release/v3.0.0` / `main`.  
**Battery:** [`BATTERY_RESULTS_v3.md`](BATTERY_RESULTS_v3.md) · **Matrix:** [`RELEASE_TEST_MATRIX_v3.md`](RELEASE_TEST_MATRIX_v3.md)

Install once:

```bash
pip install 'verityngn[deep]'
# optional CEO / delivery sensors:
# pip install 'verityngn[predictions]'
```

Set Vertex / search keys from `.env.example`. Prefer `VERTEX_LOCATION=global`.

---

## 1. Lipozem — consumer CRAAP (YouTube)

| Field | Value |
|-------|-------|
| Video | https://www.youtube.com/watch?v=tLJC8hkK-ao |
| Lane | `consumer_craap` · CRAAP §9 · Deep Research |
| Proven | 39–40 claims · `outputs/release_v3_lipozem` |

```bash
verityngn analyze --tier full --deep \
  'https://www.youtube.com/watch?v=tLJC8hkK-ao' \
  -o outputs/release_v3_lipozem
```

Gallery proof: https://verityindex.com/gallery

---

## 2. SB1507 — analyst SIFT (local file)

Chris Schuermyer’s Oregon QSBS / SB 1507 walkthrough. **Chris approved public release of the report.** The source mp4 stays out of git — place it locally (for example `~/Downloads/sb1507.mp4`) and point `-f` at that path.

| Field | Value |
|-------|-------|
| Source | Local `sb1507.mp4` (not in the repo) |
| Lane | `analyst_sift` · SIFT §9 · risk chips |
| Proven | 50 extracted → 40 verified · §6.1 = 16/40 · quant→inference 88.9% · scorecard `all_green` |
| Local artifact | `outputs/release_v3_sb1507_dense/` |

```bash
verityngn analyze --tier local-full --deep \
  -f /path/to/sb1507.mp4 \
  -o outputs/release_v3_sb1507_dense
```

Offline scorecard (no Vertex):

```bash
python scripts/sb1507_risk_taxonomy_scorecard.py
```

---

## 3. Nadella / Stargate — CEO talking-head (YouTube)

| Field | Value |
|-------|-------|
| Video | https://www.youtube.com/watch?v=lb_ZJylekWo |
| Lane | CEO extract · Primary-10 row 7 |
| Proven | 19 claims · `outputs/release_v3_battery_2026-10-18/lb_ZJylekWo/` |

```bash
verityngn analyze --tier full --deep \
  'https://www.youtube.com/watch?v=lb_ZJylekWo' \
  -o outputs/examples/lb_ZJylekWo
```

---

## What is not in this wheel

| Surface | Where it lives |
|---------|----------------|
| `verityngn[predictions]` sensors (S00–S15) | Optional OSS extra — not the default `analyze` path |
| Disclosure matcher / ClearFactor | Planned `verityngn[disclosure]` + public `rfkit` after Derrick’s `OPEN_CLOSED.md` review — empty extra in 3.0.0 |
| SplitRisk Signals Lab | Separate commercial sleeve (`~/proj/commercial/splitrisk`) — not an OSS extra |
| Hosted gallery / billing | https://verityindex.com (pins a commercial image of this engine) |

Limits that still apply: English-first; not a lie detector; not allocation alpha; no crawl / surveil product.

## Deck

Release deck with four real-run example slides: [`docs/launch/decks/`](decks/) (`VerityNgn_3_Release_with_examples.pptx` / `.pdf`, 22 pages). Rebuild: `python scripts/decks/add_oss_examples.py` (needs Chrome + LibreOffice).
