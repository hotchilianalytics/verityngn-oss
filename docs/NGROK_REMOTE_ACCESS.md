# ngrok Remote Access Setup

This guide explains how to expose your local VerityNgn API to the internet using ngrok, enabling access from:
- **Streamlit Community Cloud**: Connect your deployed UI to your local API
- **Google Colab**: Run verification notebooks that call your local API
- **Remote Testing**: Access your API from anywhere

## Prerequisites

1. **ngrok installed**: Download from [ngrok.com/download](https://ngrok.com/download)
   ```bash
   # macOS
   brew install ngrok
   
   # Linux
   snap install ngrok
   
   # Windows
   choco install ngrok
   ```

2. **ngrok account** (free): Sign up at [ngrok.com](https://ngrok.com)

3. **Configure authtoken** (one-time setup):
   ```bash
   # Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken
   ngrok authtoken YOUR_TOKEN_HERE
   ```

## Quick Start

### 1. Start the API locally

```bash
# Using Docker Compose (recommended)
docker compose up api

# OR run directly
python -m verityngn.api
```

Verify API is running:
```bash
curl http://localhost:8080/health
# Should return: &#123;"status": "healthy"&#125;
```

### 2. Start the ngrok tunnel

```bash
# Using the convenience script
./scripts/start_ngrok_tunnel.sh

# OR manually
ngrok http 8080
```

### 3. Get your public URL

Look for the **Forwarding** line in the ngrok output:

```
Forwarding    https://abc123.ngrok-free.app -> http://localhost:8080
```

Your public API URL is: `https://abc123.ngrok-free.app`

### 4. Test the tunnel

```bash
# Replace with your ngrok URL
curl https://abc123.ngrok-free.app/health
# Should return: &#123;"status": "healthy"&#125;
```

## Usage Examples

### Streamlit Community Cloud

1. Deploy your UI to Streamlit Community Cloud (see `docs/DEPLOYMENT_STREAMLIT_CLOUD.md`)

2. Add your ngrok URL to Streamlit secrets:
   ```toml
   # In Streamlit Cloud dashboard: Settings → Secrets
   VERITYNGN_API_URL = "https://abc123.ngrok-free.app"
   ```

3. Restart your Streamlit app

4. Your cloud UI will now connect to your local API!

### Google Colab

1. Update the `API_URL` in the Colab notebook:
   ```python
   # In notebooks/VerityNgn_Colab_Demo.ipynb
   API_URL = "https://abc123.ngrok-free.app"
   ```

2. Run the cells as normal

3. The notebook will call your local API through the tunnel

### Custom Applications

Use the ngrok URL as your API base:
```python
import httpx

api_url = "https://abc123.ngrok-free.app"
response = httpx.get(f"&#123;api_url&#125;/health")
print(response.json())
```

## ngrok Web Interface

ngrok provides a local web interface for monitoring requests:

- **URL**: http://localhost:4040
- **Features**:
  - Real-time request inspection
  - Request/response replay
  - Traffic statistics

## Security Considerations

⚠️ **Important Security Notes**:

1. **Public exposure**: Your local API is accessible from the internet
2. **Free plan limitations**: 
   - URLs change on restart
   - Limited requests per minute
   - Random subdomain
3. **Production**: Never use ngrok tunnels for production deployments

### Best Practices

1. **Stop the tunnel** when not in use
2. **Use authentication**: Add API keys or tokens to your API
3. **Monitor traffic**: Check the ngrok web interface (http://localhost:4040)
4. **Paid plan**: Consider ngrok Pro for:
   - Custom domains
   - Reserved URLs
   - Higher rate limits
   - Basic auth

## Troubleshooting

### ngrok: command not found

Install ngrok (see Prerequisites above)

### ngrok: authtoken not configured

```bash
# Get token from: https://dashboard.ngrok.com/get-started/your-authtoken
ngrok authtoken YOUR_TOKEN_HERE
```

### API health check fails

Verify the API is running:
```bash
# Check if API is running
curl http://localhost:8080/health

# Check Docker containers
docker compose ps

# View API logs
docker compose logs api
```

### Connection refused errors

1. Ensure API is accessible locally first
2. Check firewall settings
3. Verify port 8080 is not blocked

### ngrok URL changes frequently

**Free plan**: URLs change on every restart

**Solution**: Use ngrok Pro for reserved domains, or update your configuration each time you restart ngrok

## Advanced Configuration

### Custom subdomain (ngrok Pro)

```bash
ngrok http 8080 --subdomain=my-verityngn-api
# URL will be: https://my-verityngn-api.ngrok.io
```

### Basic authentication

```bash
ngrok http 8080 --basic-auth="username:password"
```

### Custom region

```bash
# Regions: us, eu, ap, au, sa, jp, in
ngrok http 8080 --region=eu
```

### Configuration file

Create `~/.ngrok2/ngrok.yml`:
```yaml
version: "2"
authtoken: YOUR_TOKEN_HERE
tunnels:
  verityngn:
    proto: http
    addr: 8080
    subdomain: my-verityngn-api  # Requires paid plan
    inspect: true
```

Start with:
```bash
ngrok start verityngn
```

## Alternative Solutions

If ngrok doesn't work for your use case:

1. **Cloud deployment**: Deploy API to Cloud Run (see `docs/DEPLOYMENT_CLOUD_RUN.md`)
2. **localtunnel**: Similar to ngrok, open source
3. **SSH tunneling**: Use your own server as a proxy
4. **VPN**: Use Tailscale or WireGuard for secure private access

## Support

- ngrok documentation: https://ngrok.com/docs
- VerityNgn issues: https://github.com/yourusername/verityngn-oss/issues



