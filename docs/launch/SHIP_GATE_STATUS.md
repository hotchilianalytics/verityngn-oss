# Ship-gate — go-now 3.0.1 (Monday Nov 23, 2026)

**Package:** `verityngn==3.0.1` on PyPI (**live**)  
**Engine tip:** `1b2cca8` · **Docs/release tip:** `12be77d` (tag `v3.0.1`) on `release/v3.0.0` / `main`  
**Yanked:** `verityngn==3.0.0` (do not advertise / pin)

## Pre-flight

| Check | Result |
|-------|--------|
| PyPI `3.0.1` | **200** — wheel + sdist; secret-scan PASS |
| PyPI `3.0.0` | **yanked** (both files) |
| Open-core / Primary-10 / SB1507 / examples | Unchanged from engine tip — PASS |
| Live gallery | https://verityindex.com/gallery |
| Packaging + release docs | Committed on `release/v3.0.0`; tagged `v3.0.1` (GitHub Latest) |
| PyPI `3.0.1` vs repo `verityngn/` | Sdist code diff-clean vs repo (local-only runtime dirs excluded) |
| Fact-checked release kit | [`docs/releases/v3.0.1/`](../releases/v3.0.1/) · corrections log checked in |

## Public install lock (all posts)

```bash
pip install 'verityngn[deep]==3.0.1'
verityngn analyze --tier full --deep 'https://www.youtube.com/watch?v=tLJC8hkK-ao'
```

Do **not** say `pip install verityngn==3.0.0`.

## Operator clicks before blast

1. ~~Commit packaging + release-pack updates on `release/v3.0.0`~~ **Done**
2. ~~Annotated tag + GitHub Release `v3.0.1`~~ **Done** (Latest) — tip may move again after final docs commit
3. Publish Substack from [`../releases/v3.0.1/verity-engine-oss-3-0-1-golden-release.md`](../releases/v3.0.1/verity-engine-oss-3-0-1-golden-release.md); replace root CTAs with the new permalink
4. Wake Streamlit only if you want a secondary CTA: https://verityngn.streamlit.app
5. Stagger posts per [`v3_release_pack/SURFACES.md`](v3_release_pack/SURFACES.md)

## See also

[`RELEASE_NOTES_v3.0.1.md`](RELEASE_NOTES_v3.0.1.md) · [`v3_release_pack/MEDIA_CHECKLIST.md`](v3_release_pack/MEDIA_CHECKLIST.md) · [`EXAMPLES.md`](EXAMPLES.md) · [`../releases/v3.0.1/CORRECTIONS_FROM_NOTEBOOK_DRAFT.md`](../releases/v3.0.1/CORRECTIONS_FROM_NOTEBOOK_DRAFT.md)
