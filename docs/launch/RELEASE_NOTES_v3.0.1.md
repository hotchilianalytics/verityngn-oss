# VerityNgn OSS v3.0.1 Release Notes

Packaging / security patch on the OSS 3.0 claim-risk engine. **Install from PyPI.** Prefer `3.0.1` over any `3.0.0` pin.

## Release

| Field | Value |
|-------|-------|
| Package | **`verityngn==3.0.1`** on PyPI |
| Engine tip | Monday OSS cut `1b2cca8` · Docs/release tip `f6aeb2e` (tag `v3.0.1`) |
| Branch | `release/v3.0.0` |
| Primary-10 | PASS ([`BATTERY_RESULTS_v3.md`](BATTERY_RESULTS_v3.md)) |
| Examples | [`EXAMPLES.md`](EXAMPLES.md) |
| Prior notes | [`RELEASE_NOTES_v3.0.0.md`](RELEASE_NOTES_v3.0.0.md) |

## Why 3.0.1

- **PyPI publish of the 3.0 engine** with a clean wheel/sdist.
- **Stop packaging local credential JSON** (`config/*.json` removed from setuptools `package-data`; `MANIFEST.in` excludes SA files).
- **`verityngn==3.0.0` yanked** on PyPI (packaging hygiene). Do not pin `3.0.0`.
- Publish script refuses upload if credential material appears in `dist/`.

Feature surface is the same as the 3.0 engine cut (tiers, Deep Research, CRAAP/SIFT, predictions sleeve, examples) — plus the multimodal risk surfaces that were always in that cut and are now pitched accurately for the **Monday Nov 23, 2026** launch:

| Default-on in 3.0.1 | Proof / artifact |
|---------------------|------------------|
| Adaptive **1–6 fps** scene sampling | `adaptive_sampler` scene classes |
| Pixel modalities (`visual_text` / `graphic` / `chart` / `demonstration`) | **81** pixel-only claims across 10 release runs (69 within the final primary-10); **18/40 (45%)** on SB1507; 5 Lipozem silent cards |
| `brand_safety_scores.json` | visual-only high-risk, credential-flash, blink-disclosure |
| `{video_id}_exhibit_map.json` | Bates / OCR ledger |
| Deep Research `visual_only_claims` | `--deep` lead section |

**Opt-in (same wheel):** `verityngn[vision|audio|predictions]`, `MULTISENSE_ENABLED=1`, `VN_AGENTIC_VIDEO=1`, AuthenticityGate.  
**Roadmap:** 3.1 object/action semantics + visual–spoken contradiction · 3.2 pose/lip/audio congruence default-on. Brief: [`v3_release_pack/MULTIMODAL_AND_FUTURES_v3.md`](v3_release_pack/MULTIMODAL_AND_FUTURES_v3.md).

## Install

```bash
pip install 'verityngn[deep]==3.0.1'
# optional sleeves already in the wheel:
# pip install 'verityngn[vision,audio,predictions]==3.0.1'
verityngn analyze --tier full --deep 'https://www.youtube.com/watch?v=tLJC8hkK-ao'
verityngn captions 'https://www.youtube.com/watch?v=tLJC8hkK-ao'
```

From source (after pull of the packaging commits):

```bash
pip install -e '.[deep,vision,audio]'
```

## Environment

Same as 3.0.0 — see [`RELEASE_NOTES_v3.0.0.md`](RELEASE_NOTES_v3.0.0.md). Keep GCP SA JSON **outside** the installable package tree (e.g. `~/proj/secrets/verityngn/`). Set `GOOGLE_APPLICATION_CREDENTIALS` to that path.

## Proof

- Gallery: https://verityindex.com/gallery  
- PyPI: https://pypi.org/project/verityngn/3.0.1/  
- GitHub engine cut: https://github.com/hotchilianalytics/verityngn-oss/releases/tag/v3.0.1  

## Artifacts

- Media pack: [`v3_release_pack/`](v3_release_pack/README.md)  
- Ship gate: [`SHIP_GATE_STATUS.md`](SHIP_GATE_STATUS.md)  
