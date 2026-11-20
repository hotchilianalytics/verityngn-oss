# Ship-gate — go-now 3.0.1 (10–11 Nov 2026)

**Package:** `verityngn==3.0.1` on PyPI (**live**)  
**Engine tip:** `1b2cca8` (tag `v3.0.0`) + packaging hardening on `release/v3.0.0`  
**Yanked:** `verityngn==3.0.0` (do not advertise / pin)

## Pre-flight

| Check | Result |
|-------|--------|
| PyPI `3.0.1` | **200** — wheel + sdist; secret-scan PASS |
| PyPI `3.0.0` | **yanked** (both files) |
| Open-core / Primary-10 / SB1507 / examples | Unchanged from Monday tip — PASS |
| Live gallery | https://verityindex.com/gallery |
| Packaging commits on branch | Committed on `release/v3.0.0`; tagged `v3.0.1` (GitHub release) |
| PyPI `3.0.1` vs repo `verityngn/` | Sdist code diff-clean vs repo (local-only runtime dirs excluded) |

## Public install lock (all posts)

```bash
pip install 'verityngn[deep]==3.0.1'
verityngn analyze --tier full --deep 'https://www.youtube.com/watch?v=tLJC8hkK-ao'
```

Do **not** say `pip install verityngn==3.0.0`.

## Operator clicks before blast

1. Commit packaging + release-pack updates on `release/v3.0.0` (when ready)
2. Optional: annotated tag + GitHub Release `v3.0.1` pointing at that commit (PyPI already live)
3. Wake Streamlit only if you want a secondary CTA: https://verityngn.streamlit.app
4. Stagger posts per [`v3_release_pack/SURFACES.md`](v3_release_pack/SURFACES.md)

## See also

[`RELEASE_NOTES_v3.0.1.md`](RELEASE_NOTES_v3.0.1.md) · [`v3_release_pack/MEDIA_CHECKLIST.md`](v3_release_pack/MEDIA_CHECKLIST.md) · [`EXAMPLES.md`](EXAMPLES.md)
