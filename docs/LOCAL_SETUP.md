# Local-First Setup Guide

This guide describes how to set up and run VerityNgn locally for development, research, or personal use.

## 1. Prerequisites

- **Python 3.12+**
- **Conda** (recommended) or **pip**
- **FFmpeg** (for video processing)
  - macOS: `brew install ffmpeg`
  - Ubuntu: `sudo apt-get install ffmpeg`
- **Google Cloud Project** (if using Vertex AI models)
- **Custom Search API Key** (for evidence gathering)

## 2. Installation

```bash
# Clone the repository
git clone https://github.com/hotchilianalytics/verityngn-oss.git
cd verityngn-oss

# Create environment
conda env create -f environment.yml
conda activate verityngn

# Install in editable mode
pip install -e .
```

## 3. Configuration

VerityNgn uses a `config.yaml` file for all settings.

```bash
# Copy the example config
cp config.yaml.example config.yaml
```

Edit `config.yaml` with your preferred settings:

### LLM Models (Vertex AI / Gemini)
By default, VerityNgn uses `gemini-2.5-flash` via Vertex AI.
```yaml
models:
  vertex:
    model_name: "gemini-2.5-flash"
    location: "us-central1"
```

### Authentication
VerityNgn supports several authentication modes:
- `adc`: Application Default Credentials (recommended for local)
- `service_account`: Using a JSON key file
- `none`: No authentication (useful for browsing existing reports)

```yaml
auth:
  method: "adc"
```

### Storage
Reports are saved locally by default.
```yaml
storage:
  backend: "local"
  local_dir: "./outputs"
```

## 4. Running the UI

The Streamlit UI is the easiest way to interact with VerityNgn.

```bash
streamlit run ui/streamlit_app.py
```

Access the UI at: `http://localhost:8501`

## 5. Running via CLI

You can also run verifications directly from the command line:

```bash
python run_workflow.py https://www.youtube.com/watch?v=VIDEO_ID
```

## 6. LLM Transparency Logging

VerityNgn can log all LLM interactions for analysis:

1. Enable logging in `config.yaml`:
```yaml
llm_logging:
  enabled: true
  log_dir: "./llm_logs"
```

2. View logs in the `llm_logs/` directory.

## 7. Troubleshooting

- **FFmpeg not found**: Ensure `ffmpeg` is in your PATH.
- **Quota Exceeded**: Check your Google Cloud and Search API quotas.
- **Authentication Error**: Run `gcloud auth application-default login` if using `adc` mode.

For more details, see the [Main README](../README.md).
