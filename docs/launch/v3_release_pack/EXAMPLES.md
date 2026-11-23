# VerityNgn 3.0.1 — runnable examples

Public copy-paste fixtures for the OSS 3.0 launch (**Monday Nov 23, 2026**).  
**Package:** `verityngn==3.0.1` on PyPI · engine tip `1b2cca8` · docs tip `f6aeb2e`.  
**Battery:** [`BATTERY_RESULTS_v3.md`](BATTERY_RESULTS_v3.md) · **Matrix:** [`RELEASE_TEST_MATRIX_v3.md`](RELEASE_TEST_MATRIX_v3.md) · **Notes:** [`RELEASE_NOTES_v3.0.1.md`](RELEASE_NOTES_v3.0.1.md) · **Multimodal:** [`v3_release_pack/MULTIMODAL_AND_FUTURES_v3.md`](v3_release_pack/MULTIMODAL_AND_FUTURES_v3.md)

Install once:

```bash
pip install 'verityngn[deep]==3.0.1'
# optional sleeves already in the wheel:
# pip install 'verityngn[vision,audio,predictions]==3.0.1'
```

Set Vertex / search keys from `.env.example`. Prefer `VERTEX_LOCATION=global`.

Full runs auto-emit `brand_safety_scores.json` and `{video_id}_exhibit_map.json`. Pixel claims across 10 release runs: **81** claims (69 within the final primary-10) (`visual_text`/`graphic`/`chart`/`demonstration`). Roadmap: **3.1** object/action semantics + visual–spoken contradiction · **3.2** pose/lip/audio congruence.

---

## 1. Lipozem — consumer CRAAP (YouTube)

| Field | Value |
|-------|-------|
| Video | https://www.youtube.com/watch?v=tLJC8hkK-ao |
| Lane | `consumer_craap` · CRAAP §9 · Deep Research |
| Proven | 39–40 claims · **5** silent testimonial/doctor-authority pixel cards · `outputs/release_v3_lipozem` |

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
| Proven | 50 extracted → 40 verified · **18/40 (45%) pixel-only** from slides/charts/tables · §6.1 = 16/40 · quant→inference 88.9% · scorecard `all_green` |
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
| Disclosure matcher / ClearFactor | Planned `verityngn[disclosure]` + public `rfkit` after Derrick’s `OPEN_CLOSED.md` review — empty extra in 3.0.1 |
| SplitRisk Signals Lab | Separate commercial sleeve (`~/proj/commercial/splitrisk`) — not an OSS extra |
| Hosted gallery / billing | https://verityindex.com (pins a commercial image of this engine) |

Limits that still apply: English-first; not a lie detector; not allocation alpha; no crawl / surveil product.

## Deck

Release deck with four real-run example slides: [`docs/launch/decks/`](decks/) (`VerityNgn_3_Release_with_examples.pptx` / `.pdf`, 22 pages). Rebuild: `python scripts/decks/add_oss_examples.py` (needs Chrome + LibreOffice).
