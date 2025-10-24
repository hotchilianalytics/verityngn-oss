# VerityNgn Streamlit UI

Interactive web interface for YouTube video verification.

## 🚀 Quick Start

### Install Dependencies

```bash
pip install streamlit>=1.28.0
# Or install all dependencies
pip install -r requirements.txt
```

### Run the UI

```bash
streamlit run ui/streamlit_app.py
```

The UI will open in your browser at `http://localhost:8501`.

## 📱 Features

### 1. Video Input Tab 🎬
- Enter YouTube URL for verification
- Configure model settings
- Advanced options (temperature, max claims, output formats)
- View recent verifications
- Load example videos

### 2. Processing Tab ⚙️
- Real-time workflow progress
- Stage indicators (download → analyze → verify → report)
- Workflow logs with timestamps
- Cancel/retry options
- Resource monitoring

### 3. Report Viewer Tab 📊
- Browse all verification reports
- Interactive claims table with probability distributions
- Executive summary with key findings
- Claims distribution visualization
- Download reports (JSON, Markdown, HTML)
- HTML report preview
- Delete reports

### 4. Gallery Tab 🖼️
- Browse community example verifications
- Filter by category (Health, Finance, Science, etc.)
- Search and sort examples
- Submit your reports to gallery
- View gallery statistics

### 5. Settings Tab ⚙️
- **Authentication:** Configure ADC, service account, or workload identity
- **Model Config:** Select model, temperature, tokens, cost estimates
- **Processing:** Segment FPS, claims range, search API keys
- **Output:** Formats, directories, timestamps
- **Advanced:** LLM logging, performance tuning, debug mode
- Export/import configuration

## 🎨 UI Components

The UI is modular, with each tab in its own component:

```
ui/
├── streamlit_app.py          # Main application
├── components/
│   ├── __init__.py
│   ├── video_input.py        # Video submission
│   ├── processing.py         # Progress monitoring
│   ├── report_viewer.py      # Report display
│   ├── gallery.py            # Example gallery
│   └── settings.py           # Configuration
└── README.md                 # This file
```

## 🔧 Configuration

The UI reads configuration from:
1. `config.yaml` (if exists)
2. Environment variables (`VERITYNGN_*`)
3. Session state (UI overrides)

## 💡 Usage Tips

### First Time Setup

1. **Configure Authentication:**
   - Go to Settings → Authentication
   - Choose ADC (easiest for local dev)
   - Run `gcloud auth application-default login`

2. **Set GCP Project:**
   - Go to Settings → Authentication
   - Enter your GCP Project ID

3. **Add Search API Keys:**
   - Go to Settings → Processing
   - Enter Google Search API Key and CSE ID

4. **Test with Example:**
   - Go to Verify Video tab
   - Click "Load Example 1"
   - Click "Start Verification"
   - Monitor progress in Processing tab

### Processing Videos

**For Short Videos (<5 min):**
- Use default settings
- Should complete in 2-5 minutes

**For Long Videos (>30 min):**
- Increase max_claims in Advanced Options
- May take 10-30 minutes
- Monitor in Processing tab

### Viewing Reports

1. Go to View Reports tab
2. Select report from dropdown
3. View different sections:
   - **Claims:** Detailed verification of each claim
   - **Summary:** Key findings and visualizations
   - **Raw JSON:** Full report data
   - **Download:** Export in multiple formats

### Gallery Submissions

To submit a verified video to the gallery:
1. Complete verification
2. Go to Gallery tab
3. Expand "Submit to Gallery"
4. Enter video ID, category, tags
5. Agree to CC BY 4.0 license
6. Submit (will be reviewed before publication)

## 🐛 Troubleshooting

### "Failed to load configuration"
- Ensure `config.yaml.example` exists
- Copy to `config.yaml` and configure
- Or set environment variables

### "ADC not found"
- Run: `gcloud auth application-default login`
- Ensure you have gcloud CLI installed

### "Processing stuck"
- Check Processing tab logs for errors
- Verify API keys in Settings
- Check GCP quotas and permissions

### "No reports found"
- Complete at least one verification
- Check output directory in Settings
- Verify path permissions

## 📊 System Requirements

- **Python:** 3.9+
- **RAM:** 8GB recommended (4GB minimum)
- **Storage:** 1GB per video (temporary)
- **Network:** Stable internet for downloads/API calls

## 🔐 Security Notes

- Service account keys are never stored by the UI
- API keys are stored in session state only
- Use environment variables for sensitive data
- Clear browser cache to remove sensitive info

## 🎯 Performance Tips

1. **Use ADC for local dev** (faster than service accounts)
2. **Enable LLM logging** for debugging
3. **Adjust max_claims** based on video complexity
4. **Use gemini-2.5-flash** for speed (vs gemini-pro)
5. **Process multiple videos sequentially** (not parallel)

## 📚 Advanced Features

### Custom Styling
Edit `streamlit_app.py` to customize CSS:
```python
st.markdown("""
<style>
    .your-custom-class {
        /* your styles */
    }
</style>
""", unsafe_allow_html=True)
```

### Adding New Components
1. Create new file in `components/`
2. Define `render_your_tab()` function
3. Import in `streamlit_app.py`
4. Add to tab navigation

### Integration with Batch Processing
The UI is local-first, but can be extended to submit to Google Batch:
- Add "Submit to Batch" option in Advanced Options
- Use `services.batch.job_submitter` (if available)
- Monitor batch jobs in Processing tab

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- [ ] Better progress indicators (actual stage detection)
- [ ] Real-time log streaming
- [ ] Batch job submission UI
- [ ] User authentication
- [ ] Report comparison view
- [ ] Mobile-responsive design
- [ ] Dark mode toggle

## 📄 License

MIT License - see LICENSE file

## 🔗 Links

- [Main Documentation](../README.md)
- [Configuration Guide](../docs/guides/configuration.md)
- [API Reference](../docs/api/README.md)
- [GitHub Issues](https://github.com/.../verityngn-oss/issues)


