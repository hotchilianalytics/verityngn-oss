# Ship clicks — v3.0.0 (Monday 9 Nov 2026)

**Status:** Git tag `v3.0.0` tracks tip of `release/v3.0.0` / `main`. Examples + SB1507 public copy are in this tree. **PyPI** still needs `TWINE_PASSWORD` if the upload has not landed.

| Action | Command / note | Monday |
|--------|----------------|--------|
| Push `release/v3.0.0` | `git push -u origin HEAD` | This release ask |
| Fast-forward `main` | from `origin/main` only — never stale local `main` | This release ask |
| Retag `v3.0.0` | annotated tag on Monday tip | This release ask |
| GitHub release notes | match EXAMPLES + SB1507 public | This release ask |
| PyPI publish | `twine` with `__token__` | If token in env |
| Wake Streamlit | https://verityngn.streamlit.app | Operator click |
| Commercial pin | `94f62f6` → Monday SHA (see SHIP_GATE_STATUS) | Checklist / redeploy if gcloud authed |

**Pre-ship checklist**

1. [`RELEASE_TEST_MATRIX_v3.md`](RELEASE_TEST_MATRIX_v3.md) offline PASS  
2. Lipozem + SB1507 live PASS (done)  
3. Primary-10 PASS (done)  
4. [`EXAMPLES.md`](EXAMPLES.md) copy-paste commands match README  
5. SB1507 public (Chris approved); source mp4 **not** in git  

**Reproduce fixtures**

```bash
# See docs/launch/EXAMPLES.md
export VERTEX_LOCATION=global
verityngn analyze --tier full --deep 'https://www.youtube.com/watch?v=tLJC8hkK-ao'
verityngn analyze --tier local-full --deep -f /path/to/sb1507.mp4 -o outputs/release_v3_sb1507_dense
verityngn analyze --tier full --deep 'https://www.youtube.com/watch?v=lb_ZJylekWo'
```
