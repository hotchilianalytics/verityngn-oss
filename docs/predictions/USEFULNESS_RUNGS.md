# Usefulness rungs — U1 / U2 / U3

**Date:** 2026-08-20  
**Rule:** Do not wait for Family B (ICIR ≥ 0.40, DSR ≥ 0.95) or Power = 194 to call the panel useful. Those are allocation bars. See [GATES_GLOSSARY.md](GATES_GLOSSARY.md).

**Freeze:** No new CEOs on the fused factor until NuisanceLeak < 0.20 **and** Fidelity ≥ 0.60. Do not revert V7m.

---

## U1 — useful player risk panel (this sprint, n=7)

**Done when:**

1. **T017** — `live_gemini` on remaining six (skip `QNkPpVYagRc`). Re-score L; **keep only if L falls**.  
2. **Residualize** S01 on `n_claims` / `duration_sec` (and available nuisances). Leak on residual should leave 0.469. Do not add CEOs to fix leak.  
3. **T018** — MediaPipe Face Landmarker on local mp4s; **≥2 CNBC talking-heads** with `vision_source=mediapipe_face_landmarker`, face coverage stamped per claim. Prefer `QNkPpVYagRc`, `WBu9Ai6OX3I`, `pHu-FarYZlU`; treat `ijRuuaaM6XM` as coverage-fail.  
4. S01 rebuilt with real face terms (renormalize, never 0.5). **S12** emitted as `HFAsy_proxy` with Banker citation + “not a 1:1 replication” caveat.  
5. Panel copy: **instrument_only** until Fidelity ≥ 0.60; still **NO_PROMOTE**.

**What U1 is:** timestamped delivery-risk + provenance of every number.  
**What U1 is not:** alpha, allocation, or Oxford-Man-scale modal incongruence until face is on all rows.

---

## U2 — useful risk-abatement without 194 videos (parallel, text)

**S15** on transcripts / 10-K risk sections (Kim, Muhn & Nikolaev 2023). Path to **abnormal-vol significance** while video n is small. Powers the GC / quarterly-pack sleeve. No new vision required. Does not violate the CEO freeze on the *video* factor.

Optional audio cold-start (not a CEO add): Qin & Yang 2019 — 576 S&P 500 calls for S05/S08 calibration only.

---

## U3 — honest event-study (more videos, still underpowered)

Target **~30–50 leakage-safe CNBC pre-print talking-heads** (Banker built 205; Oxford-Man 2,439).

1. Same player first (`ceo_pltr_karp`).  
2. Then Huang / NVDA catalog (T011 stub).  
3. Report Spearman vs next-print **`raw_h1`** (honest name until market-model CAR lands) with bootstrap CIs and the **194-event caption**.  
4. Register the trial in `docs/trials_ledger.md` **before** peeking.

### CNBC catalog expansion spec

| Filter | Rule |
|--------|------|
| Venue | CNBC (or labeled conference); keep venue prior |
| Framing | Talking-head preferred; reject or flag two-shots |
| Window | `pre` print for event join; recorded date < next_print |
| Fields | Mirror `docs/karp_pre_earnings_videos.json` / Huang catalog |
| Order | Karp → Huang → Cook / Nadella → Musk (mediasphere stress only) |
| Downloads | After U1 leak + fidelity gates; yt-dlp cookies + `tv_downgraded`/`web_safari` as pinned |

**Do not** wait for ICIR 0.40 / DSR 0.95 to call the panel useful.

---

## Power honesty

| Claim | n needed (approx) |
|-------|-------------------|
| Player instrumentation panel (U1) | 5–7 videos, measured sensors |
| Detect Spearman ρ = 0.20 @ 80% power | **194** events |
| Banker-style CNBC HFAsy study | 205 interviews (their sample) |
| Oxford-Man modal incongruence | 2,439 interviews |

25 CEOs × 4 prints/yr ≈ 100 video-lane bets/year; at IC = 0.03, Grinold IR ≈ 0.30. **Video is the differentiator; S15/text is the statistical engine.**
