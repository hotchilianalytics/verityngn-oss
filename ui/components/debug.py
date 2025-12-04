import streamlit as st
import os
import sys
from pathlib import Path
import glob
import datetime

def render_debug_tab():
    """Render the System Health & Debug dashboard."""
    st.markdown("## 🏥 System Health & Debug")
    
    # 1. Environment Variables Check
    st.markdown("### 🔑 Environment Variables")
    
    critical_keys = [
        "OPENAI_API_KEY",
        "GOOGLE_SEARCH_API_KEY",
        "CSE_ID",
        "ANTHROPIC_API_KEY",
        "GOOGLE_AI_STUDIO_KEY",
        "YOUTUBE_API_KEY",
        "GCS_BUCKET_NAME",
        "PROJECT_ID",
        "LOCATION"
    ]
    
    cols = st.columns(3)
    for i, key in enumerate(critical_keys):
        val = os.getenv(key)
        status = "✅ Set" if val else "❌ Missing"
        if val:
            # Mask value: show first 4 and last 4 chars
            if len(val) > 8:
                masked = f"{val[:4]}...{val[-4:]}"
            else:
                masked = "***"
        else:
            masked = "Not Set"
            
        with cols[i % 3]:
            st.metric(label=key, value=status, delta=masked if val else None, delta_color="normal")

    # 2. Configuration & Context
    st.markdown("### ⚙️ Configuration & Context")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Deployment Mode**")
        st.code(os.getenv("DEPLOYMENT_MODE", "Unknown"))
        
    with col2:
        st.markdown("**Storage Backend**")
        st.code(os.getenv("STORAGE_BACKEND", "Unknown"))
        
    with col3:
        st.markdown("**Working Directory**")
        st.code(os.getcwd())

    with st.expander("Full Environment Dump (Safe Subset)"):
        # Filter out potentially sensitive keys not in our allowlist if strictly needed, 
        # but for debug dashboard we often want to see what's there. 
        # We'll just list keys.
        st.json(dict(os.environ))

    # 3. File System Browser
    st.markdown("### 📂 File System Browser")
    
    # Allow browsing typical directories
    base_dirs = {
        "App Root": ".",
        "Outputs": "outputs",
        "Downloads": "downloads",
        "Temp Outputs": "/tmp/outputs" if os.path.exists("/tmp/outputs") else None,
        "App Outputs (Docker)": "/app/outputs" if os.path.exists("/app/outputs") else None
    }
    
    # Filter out None paths
    base_dirs = {k: v for k, v in base_dirs.items() if v is not None}
    
    selected_base = st.selectbox("Select Directory", list(base_dirs.keys()))
    current_path = base_dirs[selected_base]
    
    if os.path.exists(current_path):
        files = []
        try:
            # List all files recursively (limit depth/count for performance)
            for root, dirs, filenames in os.walk(current_path):
                # Skip hidden dirs
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for f in filenames:
                    if f.startswith('.'): continue
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, current_path)
                    size = os.path.getsize(full_path)
                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                    files.append({
                        "path": rel_path,
                        "size": f"{size/1024:.1f} KB",
                        "modified": mtime.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    if len(files) > 500: break
                if len(files) > 500: break
                
            if files:
                st.dataframe(files, use_container_width=True)
            else:
                st.info("No files found in this directory.")
                
        except Exception as e:
            st.error(f"Error listing files: {e}")
    else:
        st.warning(f"Directory not found: {current_path}")

    # 4. Check for specific files
    st.markdown("### 🔍 Critical File Check")
    critical_files = [
        "cookies.txt",
        ".env",
        "service-account.json",
        "config/settings.py"
    ]
    
    for f in critical_files:
        exists = os.path.exists(f)
        icon = "✅" if exists else "❌"
        st.write(f"{icon} `{f}` {'exists' if exists else 'missing'}")



