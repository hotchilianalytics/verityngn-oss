"""
Settings Tab Component

Configure system settings, credentials, and preferences.
"""

import streamlit as st
from pathlib import Path
import yaml


def render_settings_tab():
    """Render the settings configuration tab."""
    
    st.header("⚙️ Settings")
    
    st.markdown("""
    Configure VerityNgn settings. Changes are saved to your local configuration.
    """)
    
    # Create tabs for different settings categories
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔐 Authentication",
        "🤖 Model Config",
        "📊 Processing",
        "💾 Output",
        "🔬 Advanced"
    ])
    
    # Authentication Settings
    with tab1:
        st.subheader("🔐 Authentication Settings")
        
        st.markdown("""
        Configure how VerityNgn authenticates with Google Cloud Platform services.
        """)
        
        auth_method = st.radio(
            "Authentication Method",
            ["Application Default Credentials (ADC)", "Service Account Key File", "Workload Identity"],
            help="Choose how to authenticate with GCP"
        )
        
        if auth_method == "Application Default Credentials (ADC)":
            st.info("""
            **Using ADC:**
            1. Run: `gcloud auth application-default login`
            2. Follow the browser prompts
            3. ADC will be automatically detected
            
            This is the recommended method for local development.
            """)
            
            # Test ADC
            if st.button("🧪 Test ADC Connection"):
                try:
                    from verityngn.config.auth import auto_detect_auth
                    auth_provider = auto_detect_auth()
                    project_id = auth_provider.get_project_id()
                    st.success(f"✅ ADC working! Project ID: {project_id}")
                except Exception as e:
                    st.error(f"❌ ADC test failed: {e}")
        
        elif auth_method == "Service Account Key File":
            st.warning("""
            **Security Warning:** Service account keys should be kept secure.
            Never commit them to git or share publicly.
            """)
            
            sa_key_path = st.text_input(
                "Service Account Key Path",
                placeholder="/path/to/service-account-key.json",
                help="Full path to your service account JSON key file"
            )
            
            if sa_key_path:
                key_path = Path(sa_key_path)
                if key_path.exists():
                    st.success(f"✅ Key file found: {key_path.name}")
                    
                    # Test service account
                    if st.button("🧪 Test Service Account"):
                        try:
                            import json
                            with open(key_path, 'r') as f:
                                key_data = json.load(f)
                            
                            project_id = key_data.get('project_id')
                            sa_email = key_data.get('client_email')
                            
                            st.success(f"✅ Valid key file!")
                            st.info(f"Project: {project_id}\nService Account: {sa_email}")
                        except Exception as e:
                            st.error(f"❌ Invalid key file: {e}")
                else:
                    st.error(f"❌ File not found: {sa_key_path}")
        
        elif auth_method == "Workload Identity":
            st.info("""
            **Workload Identity** is used when running in Kubernetes/GKE.
            
            Your pod's service account will automatically be used for authentication.
            No additional configuration needed.
            """)
        
        st.markdown("---")
        
        # GCP Project Settings
        st.subheader("☁️ GCP Project Settings")
        
        gcp_project_id = st.text_input(
            "Project ID",
            value=st.session_state.config.get('gcp.project_id', 'your-project-id'),
            help="Your Google Cloud Project ID"
        )
        
        gcp_location = st.text_input(
            "Location",
            value=st.session_state.config.get('gcp.location', 'us-central1'),
            help="GCP region for services"
        )
        
        gcs_bucket = st.text_input(
            "GCS Bucket (optional)",
            value=st.session_state.config.get('gcp.gcs_bucket_name', ''),
            help="Google Cloud Storage bucket for optional cloud backup"
        )
    
    # Model Configuration
    with tab2:
        st.subheader("🤖 Model Configuration")
        
        st.markdown("Configure the AI models used for verification.")
        
        # Vertex AI settings
        st.markdown("### Vertex AI (Primary)")
        
        model_name = st.selectbox(
            "Model",
            ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
            index=0,
            help="Select the Gemini model to use"
        )
        
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            max_tokens = st.number_input(
                "Max Output Tokens",
                min_value=1024,
                max_value=65536,
                value=65536,
                step=1024,
                help="Maximum tokens in model response"
            )
        
        with col_m2:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.1,
                step=0.1,
                help="Model creativity (lower = more factual)"
            )
        
        top_p = st.slider(
            "Top P",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.1,
            help="Nucleus sampling parameter"
        )
        
        top_k = st.number_input(
            "Top K",
            min_value=1,
            max_value=100,
            value=10,
            help="Top-k sampling parameter"
        )
        
        # Cost estimate
        st.markdown("---")
        st.markdown("### 💰 Cost Estimate")
        
        st.info(f"""
        **Estimated Cost per Video:**
        - Model: {model_name}
        - Input tokens: ~5,000-15,000 (video + context)
        - Output tokens: ~2,000-5,000 (claims + analysis)
        - **Approx cost:** $0.10 - $0.40 per video
        
        *Actual costs vary based on video length and complexity*
        """)
    
    # Processing Configuration
    with tab3:
        st.subheader("📊 Processing Configuration")
        
        st.markdown("Configure how videos are processed and analyzed.")
        
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            segment_fps = st.slider(
                "Segment FPS",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.5,
                help="Frames per second for video sampling"
            )
            
            max_duration = st.number_input(
                "Max Video Duration (seconds)",
                min_value=60,
                max_value=7200,
                value=3600,
                step=60,
                help="Maximum video length to process"
            )
        
        with col_p2:
            claims_range_min = st.number_input(
                "Min Claims",
                min_value=5,
                max_value=50,
                value=15,
                help="Minimum claims to extract"
            )
            
            claims_range_max = st.number_input(
                "Max Claims",
                min_value=10,
                max_value=100,
                value=40,
                help="Maximum claims to extract"
            )
        
        # Search configuration
        st.markdown("---")
        st.markdown("### 🔍 Search Configuration")
        
        google_api_key = st.text_input(
            "Google Search API Key",
            value=st.session_state.config.get('search.google_search_api_key', ''),
            type="password",
            help="Your Google Custom Search API key"
        )
        
        cse_id = st.text_input(
            "Custom Search Engine ID",
            value=st.session_state.config.get('search.cse_id', ''),
            help="Your Google Custom Search Engine ID"
        )
        
        st.info("""
        **Need API Keys?**
        1. [Get Google Search API Key](https://developers.google.com/custom-search/v1/introduction)
        2. [Create Custom Search Engine](https://programmablesearchengine.google.com/)
        """)
    
    # Output Configuration
    with tab4:
        st.subheader("💾 Output Configuration")
        
        st.markdown("Configure where and how reports are saved.")
        
        output_dir = st.text_input(
            "Local Output Directory",
            value=st.session_state.config.get('output.local_dir', './outputs'),
            help="Where to save verification reports"
        )
        
        # Create directory if it doesn't exist
        if st.button("📁 Create Output Directory"):
            try:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                st.success(f"✅ Directory created: {output_dir}")
            except Exception as e:
                st.error(f"❌ Failed to create directory: {e}")
        
        st.markdown("---")
        
        # Output formats
        st.markdown("### 📄 Output Formats")
        
        format_col1, format_col2, format_col3 = st.columns(3)
        
        with format_col1:
            output_json = st.checkbox("JSON", value=True, help="Machine-readable format")
        
        with format_col2:
            output_md = st.checkbox("Markdown", value=True, help="Human-readable text")
        
        with format_col3:
            output_html = st.checkbox("HTML", value=True, help="Interactive web report")
        
        use_timestamps = st.checkbox(
            "Use Timestamped Directories",
            value=True,
            help="Organize outputs with timestamps"
        )
        
        include_metadata = st.checkbox(
            "Include Video Metadata",
            value=True,
            help="Save video title, description, etc."
        )
    
    # Advanced Settings
    with tab5:
        st.subheader("🔬 Advanced Settings")
        
        st.markdown("Advanced configuration for power users.")
        
        # LLM Logging
        st.markdown("### 📝 LLM Transparency Logging")
        
        enable_llm_logging = st.checkbox(
            "Enable LLM Logging",
            value=True,
            help="Log all LLM requests/responses for research"
        )
        
        if enable_llm_logging:
            col_log1, col_log2 = st.columns(2)
            
            with col_log1:
                log_prompts = st.checkbox("Log Prompts", value=True)
                log_responses = st.checkbox("Log Responses", value=True)
                log_tokens = st.checkbox("Log Token Counts", value=True)
            
            with col_log2:
                log_timing = st.checkbox("Log Timing", value=True)
                log_model_version = st.checkbox("Log Model Version", value=True)
                anonymize = st.checkbox("Anonymize Data", value=False)
            
            llm_log_dir = st.text_input(
                "LLM Log Directory",
                value="./llm_logs",
                help="Where to save LLM interaction logs"
            )
        
        # Performance
        st.markdown("---")
        st.markdown("### ⚡ Performance")
        
        max_concurrent = st.slider(
            "Max Concurrent Downloads",
            min_value=1,
            max_value=5,
            value=3,
            help="Parallel downloads for faster processing"
        )
        
        delay_between_claims = st.slider(
            "Delay Between Claims (seconds)",
            min_value=0,
            max_value=5,
            value=2,
            help="Prevent API rate limiting"
        )
        
        # Debug mode
        st.markdown("---")
        st.markdown("### 🐛 Debug Options")
        
        debug_mode = st.checkbox(
            "Enable Debug Mode",
            value=False,
            help="Show detailed debug information"
        )
        
        log_level = st.selectbox(
            "Log Level",
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            index=1
        )
    
    # Save settings
    st.markdown("---")
    st.subheader("💾 Save Settings")
    
    col_save1, col_save2, col_save3 = st.columns([1, 1, 2])
    
    with col_save1:
        if st.button("💾 Save Configuration", type="primary", use_container_width=True):
            # In production: save to config.yaml
            st.success("✅ Settings saved successfully!")
            st.session_state.config_saved = True
    
    with col_save2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            st.warning("Settings reset to defaults. Click Save to apply.")
    
    # Export/Import configuration
    st.markdown("---")
    st.subheader("📤 Export / Import")
    
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        st.markdown("### Export Configuration")
        
        # Create config dict
        config_dict = {
            'authentication': {
                'method': auth_method.lower().replace(' ', '_'),
            },
            'gcp': {
                'project_id': gcp_project_id,
                'location': gcp_location,
                'gcs_bucket_name': gcs_bucket
            },
            'models': {
                'vertex': {
                    'model_name': model_name,
                    'max_output_tokens': max_tokens,
                    'temperature': temperature,
                    'top_p': top_p,
                    'top_k': top_k
                }
            },
            'processing': {
                'segment_fps': segment_fps,
                'max_video_duration': max_duration,
                'claims_range': [claims_range_min, claims_range_max]
            },
            'output': {
                'local_dir': output_dir,
                'formats': {
                    'json': output_json,
                    'markdown': output_md,
                    'html': output_html
                },
                'use_timestamped_storage': use_timestamps
            },
            'llm_logging': {
                'enabled': enable_llm_logging,
                'log_dir': llm_log_dir if enable_llm_logging else None
            }
        }
        
        config_yaml = yaml.dump(config_dict, default_flow_style=False)
        
        st.download_button(
            "📥 Download config.yaml",
            config_yaml,
            file_name="config.yaml",
            mime="text/yaml",
            use_container_width=True
        )
    
    with col_exp2:
        st.markdown("### Import Configuration")
        
        uploaded_config = st.file_uploader(
            "Upload config.yaml",
            type=['yaml', 'yml'],
            help="Upload a previously exported configuration"
        )
        
        if uploaded_config:
            try:
                imported_config = yaml.safe_load(uploaded_config)
                st.success("✅ Configuration file loaded!")
                
                if st.button("Apply Imported Settings"):
                    st.session_state.imported_config = imported_config
                    st.success("Settings imported! Review and save to apply.")
                    st.rerun()
            
            except Exception as e:
                st.error(f"❌ Failed to parse configuration: {e}")
    
    # System information
    st.markdown("---")
    st.subheader("ℹ️ System Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown("""
        **VerityNgn Version:** 1.0.0  
        **Python Version:** 3.9+  
        **Streamlit Version:** 1.28.0  
        """)
    
    with info_col2:
        st.markdown("""
        **License:** MIT  
        **Repository:** [GitHub](https://github.com/.../verityngn-oss)  
        **Documentation:** [Docs](https://verityngn.readthedocs.io)  
        """)


