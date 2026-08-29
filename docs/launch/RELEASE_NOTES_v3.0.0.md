# VerityNgn OSS v3.0.0 Release Notes

Standalone Apache-2.0 multimodal video claim verification engine with Deep Research.

## Highlights

- Deep Research (`verityngn analyze --deep`) in OSS
- Authenticity gate stubs + spectral AI-voice cues + MediaPipe Face Landmarker
- Open-core docs: `docs/OPEN_CORE.md`, `docs/DEPENDENCY_MODEL.md`
- Boundary CI scrub (no predictions/quant in package)
- Release paper + charts: `papers/verityngn_oss_v3_release.{md,pdf}`

## Install

```bash
pip install 'verityngn==3.0.0'
# from source: pip install -e '.[deep,vision,audio]'
verityngn analyze <url> --deep
```

## Docker

```bash
docker build -f Dockerfile.api -t verityngn-oss:v3.0.0 .
docker build -f Dockerfile.batch -t verityngn-oss-batch:v3.0.0 .
```

## Not included

Predictions, RiskFactor S00–S15, hosted trial/credits SaaS.

## Artifacts

- PDF: `papers/verityngn_oss_v3_release.pdf`
- Parity checklist: `PARITY_TEST_v3.md`
