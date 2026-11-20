# LinkedIn — VerityNgn OSS 3.0.1

Attach: `papers/figures/open_core_architecture.png` (or `platform_layers.png`).

We just cut **VerityNgn OSS 3.0.1** (public launch **Monday, Nov 16, 2026**): an Apache-2.0 multimodal engine for **claim-level risk abatement** on video — adaptive **1–6 fps** sampling, pixel claims, auto-emitted `brand_safety_scores.json` + exhibit maps, Deep Research in the public CLI, analyst SIFT vs consumer CRAAP, and a documented morph from “truthfulness report” to a layered **risk platform**.

**Pixel proof:** 45% of SB1507 claims and Lipozem’s doctor/weight-loss cards exist only in pixels — transcript-only tools miss them. 81 verified pixel-only claims across the v3 release benchmark.

Public proof (hosted gallery): https://verityindex.com/gallery  

Install from PyPI: `pip install 'verityngn[deep]==3.0.1'`  
`verityngn analyze <url> --deep` · local files via `--tier local-full -f clip.mp4`

**Roadmap:** 3.1 object/action semantics + visual–spoken contradiction; 3.2 pose/lip/audio congruence atop MediaPipe + MultiSense sleeves already in the wheel — delivery/disclosure risk, never lie detection.

Open-core, on purpose: engine + research sleeves stay OSS. **verityindex.com** is the hosted control plane. ClearFactor disclosure services sit on that plane. No earnings-alpha marketing.

Primary-10 PASS · multimodal brief `MULTIMODAL_AND_FUTURES_v3.md` · paper `papers/verityngn_oss_v3_release.md` · PyPI: https://pypi.org/project/verityngn/3.0.1/

#OpenSource #OSINT #RiskManagement #AI #Video
