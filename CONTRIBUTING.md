# Contributing

Thanks for your interest in contributing to VerityNgn.

## Quick start

1. Fork the repo and create a feature branch.
2. Follow the local setup in `README.md`.
3. Make a focused change with a clear commit message.
4. Open a PR describing:
   - What changed
   - Why it changed
   - How to test it

## Development setup

### Environment
- Copy `env.example` to `.env` (local development) or set environment variables.
- Never commit secrets. See `SECURITY.md`.

### Run Streamlit UI (local)
Follow the “Quick Start” in `README.md`.

## Pull request guidelines

- Keep PRs small and reviewable.
- Add/adjust docs when behavior changes.
- Prefer explicit error messages over silent failures.
- Avoid adding new required secrets without updating `env.example` and Streamlit secrets examples.

## Security

Do not report vulnerabilities via GitHub issues. Use the process in `SECURITY.md`.


