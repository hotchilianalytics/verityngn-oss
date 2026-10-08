# Ship clicks — v3.0.0 (gated)

**Status:** Not executed. Awaiting **explicit operator ask** after matrix green (or operator accepts PENDING primary-10 expansion).

| Action | Command / note | Allowed now? |
|--------|----------------|--------------|
| Push `release/v3.0.0` | `git push -u origin HEAD` | Only on ask |
| Retag `v3.0.0` | move tag to absorb SHA `8d6a8e3` (or later battery tip) | Only on ask |
| Merge to `main` | PR or fast-forward — **never** without ask | Only on ask |
| PyPI publish | `twine` / release workflow | Only on ask |

**Pre-ship checklist**

1. [`RELEASE_TEST_MATRIX_v3.md`](RELEASE_TEST_MATRIX_v3.md) offline PASS  
2. Lipozem + SB1507 live PASS (done)  
3. Primary-10 PENDING cleared **or** operator accepts freeze carve-out  
4. Wave B blogs drafted if public launch same week  
5. Chris full HTML still gated  

**Battery when unfrozen**

```bash
export VERTEX_LOCATION=global
bash scripts/run_release_v3_battery.sh   # SKIP_PRIOR=1 by default
```
