# Browser verification — 25 October 2026

Screenshots: `docs/launch/v3_release_pack/screenshot_*.png`

| Surface | URL | Result |
|---------|-----|--------|
| Gallery | https://verityindex.com/gallery | **PASS** — Public Analysis Gallery, 14 reports, cards render |
| Streamlit demo | https://verityngn.streamlit.app | **FAIL** — Streamlit sleep / “get this app back up” |
| GitHub branch | https://github.com/hotchilianalytics/verityngn-oss/tree/release/v3.0.0 | **PASS** — public, 19 commits ahead of main |
| GitHub releases | https://github.com/hotchilianalytics/verityngn-oss/releases | **PASS** — `v3.0.0` (c740bad) Latest; `v3.0.0-candidate` pre-release. Do not retag until explicit go |

Streamlit is hosted sleep, not an engine regression. Wake it before the public launch blast.
