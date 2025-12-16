# GitHub Actions CI Workflows

This directory contains GitHub Actions workflows for continuous integration.

## Current Workflows

### `ci.yml` - Main CI Pipeline

Runs on every push to `main` and on pull requests. Performs:

1. **UI Smoke Test** - Compiles UI code to catch syntax errors
2. **Core Smoke Test** - Compiles core code and runs import tests
3. **Secret Scan** - Scans for accidentally committed secrets/credentials

## Why Conda/Mamba Instead of Pip?

The CI workflow uses **conda/mamba** instead of `pip` for dependency installation because:

1. **Complex Dependency Resolution** - Google Cloud packages and LangChain ecosystem have intricate version conflicts that conda resolves better than pip
2. **System Dependencies** - Tools like `ffmpeg` are managed by conda, not pip
3. **Production Parity** - Matches the Docker build process (`Dockerfile.api`, `Dockerfile.batch`) which also uses conda
4. **Prevents Conflicts** - Conda's solver prevents dependency conflicts that would cause CI failures

## Testing CI Locally

You can test the CI setup locally before pushing:

### Prerequisites

1. Install miniconda or mambaforge:
   ```bash
   # macOS (using Homebrew)
   brew install miniforge
   
   # Or download from: https://github.com/conda-forge/miniforge
   ```

2. Initialize conda in your shell:
   ```bash
   # Add to ~/.zshrc or ~/.bashrc
   eval "$(conda shell.bash hook)"
   ```

### Run CI Steps Locally

1. **Setup conda environment:**
   ```bash
   cd /Users/ajjc/proj/verityngn-oss
   bash scripts/ci/setup_conda_env.sh
   ```

2. **Test UI compilation:**
   ```bash
   conda activate verityngn
   pip install streamlit>=1.28.0  # UI needs streamlit for compilation
   python -m compileall -q ui
   ```

3. **Test core compilation:**
   ```bash
   conda activate verityngn
   python -m compileall -q verityngn
   ```

4. **Run import tests:**
   ```bash
   conda activate verityngn
   python test/unit/test_imports.py
   ```

5. **Run secret scan:**
   ```bash
   python scripts/ci/secret_scan.py
   ```

## Updating Dependencies

**Important:** CI uses `environment-minimal.yml`, not `requirements.txt`.

To update dependencies for CI:

1. Edit `environment-minimal.yml`
2. Test locally:
   ```bash
   conda activate verityngn
   mamba env update -f environment-minimal.yml --name verityngn
   python test/unit/test_imports.py
   ```
3. Commit and push - CI will automatically use the updated environment

## CI Cache

The workflow caches the conda environment to speed up CI runs:

- **Cache key:** Hash of `environment-minimal.yml`
- **Cache path:** `~/.conda/envs/verityngn`
- **Effect:** First run takes ~5-10 minutes, subsequent runs take ~1-2 minutes

If you need to invalidate the cache, modify `environment-minimal.yml` (even a comment change will work).

## Troubleshooting

### CI Fails with "Environment creation failed"

- Check `environment-minimal.yml` for syntax errors
- Verify all packages are available in conda-forge channel
- Test locally: `mamba env create -f environment-minimal.yml`

### CI Fails with "Import errors"

- Verify imports work locally: `python test/unit/test_imports.py`
- Check that all required packages are in `environment-minimal.yml`
- Ensure Python version matches (3.12)

### CI is Slow

- First run is always slow (~5-10 minutes) - this is normal
- Subsequent runs should be faster due to caching
- If cache isn't working, check GitHub Actions cache settings

## Workflow Structure

```
ci.yml
├── ui-smoke job
│   ├── Setup conda/mamba
│   ├── Cache environment
│   ├── Create conda environment
│   ├── Install streamlit (for UI)
│   └── Compile UI code
│
├── core-smoke job
│   ├── Setup conda/mamba
│   ├── Cache environment
│   ├── Create conda environment
│   ├── Compile core code
│   └── Run import tests
│
└── secret-scan job
    ├── Setup Python (stdlib only)
    └── Run secret scanner
```

## Related Files

- `environment-minimal.yml` - Conda environment definition for CI
- `environment.yml` - Full conda environment (for local development)
- `requirements.txt` - Pip requirements (for reference, not used in CI)
- `scripts/ci/setup_conda_env.sh` - Helper script for local testing
- `scripts/ci/secret_scan.py` - Secret scanning script

## Future Improvements

- [ ] Add matrix testing for multiple Python versions
- [ ] Add linting step (ruff, black, mypy)
- [ ] Add type checking step
- [ ] Add integration tests
- [ ] Add performance benchmarks

