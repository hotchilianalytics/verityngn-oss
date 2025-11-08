# Google Colab Deployment Guide

Run VerityNgn verifications from Google Colab notebooks.

## Quick Start

### Option 1: Use Existing API

If you have a deployed API:

1. Open the Colab notebook: [VerityNgn_Colab_Demo.ipynb](../notebooks/VerityNgn_Colab_Demo.ipynb)
2. Click "Open in Colab" badge
3. Run Setup cell
4. Set `API_URL` to your endpoint
5. Submit videos and view results

### Option 2: Local API via ngrok

To use local API from Colab:

1. On your local machine, start API:
   ```bash
   python -m verityngn.api
   ```

2. Install and run ngrok:
   ```bash
   ngrok http 8080
   ```

3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

4. In Colab, set:
   ```python
   API_URL = "https://abc123.ngrok.io"
   ```

## Notebook Structure

The demo notebook includes:
- **Setup**: Install dependencies
- **Configuration**: Set API endpoint
- **Submit**: Send video for verification
- **Monitor**: Poll for progress
- **View**: Display HTML report
- **Download**: Save reports locally

## Examples

### Basic Verification

```python
# Configure
API_URL = "https://your-api.run.app"

# Submit
VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
response = requests.post(f"{API_URL}/api/v1/verification/verify", 
                         json={"video_url": VIDEO_URL})
task_id = response.json()["task_id"]

# Monitor
while True:
    status = requests.get(f"{API_URL}/api/v1/verification/status/{task_id}")
    if status.json()["status"] == "completed":
        break
    time.sleep(5)

# Get report
report = requests.get(f"{API_URL}/api/v1/reports/{video_id}/report.html")
display(HTML(report.text))
```

## Troubleshooting

**Cannot connect to API**
- Verify API is running and accessible
- Check firewall/CORS settings
- Use ngrok for local-to-Colab connection

**Timeout errors**
- Increase timeout values
- Check video length (longer = more time)
- Monitor API logs

See [DEPLOYMENT_LOCAL.md](DEPLOYMENT_LOCAL.md) for local API setup.




