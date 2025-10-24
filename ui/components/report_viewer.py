"""
Report Viewer Tab Component

View and interact with generated verification reports.
"""

import streamlit as st
import json
from pathlib import Path
import streamlit.components.v1 as components


def load_report(video_id: str, output_dir: Path) -> dict:
    """Load report JSON for a video ID."""
    report_path = output_dir / video_id / 'report.json'
    
    if not report_path.exists():
        return None
    
    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def render_claims_table(claims: list):
    """Render claims in an interactive table."""
    if not claims:
        st.info("No claims found in this report.")
        return
    
    for i, claim in enumerate(claims, 1):
        with st.expander(f"**Claim {i}:** {claim.get('claim_text', 'N/A')[:100]}..."):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Full Claim:** {claim.get('claim_text', 'N/A')}")
                
                # Evidence summary
                st.markdown("**Evidence Summary:**")
                st.write(claim.get('evidence_summary', 'No summary available'))
                
                # Conclusion
                st.markdown("**Conclusion:**")
                st.write(claim.get('conclusion_summary', 'No conclusion available'))
            
            with col2:
                # Probability distribution
                prob_dist = claim.get('probability_distribution', {})
                
                st.markdown("**Probability Distribution:**")
                for outcome, prob in prob_dist.items():
                    if prob > 0:
                        color = "🟢" if outcome == "TRUE" else "🔴" if outcome == "FALSE" else "🟡"
                        st.metric(f"{color} {outcome}", f"{prob:.1%}")
                
                # Sources count
                sources = claim.get('sources', [])
                st.metric("Evidence Sources", len(sources))
            
            # Show sources
            if sources:
                st.markdown("**Sources:**")
                for j, source in enumerate(sources[:5], 1):  # Show first 5
                    st.markdown(f"{j}. [{source.get('title', 'Source')}]({source.get('url', '#')})")
                
                if len(sources) > 5:
                    st.caption(f"... and {len(sources) - 5} more sources")


def render_report_viewer_tab():
    """Render the report viewer tab."""
    
    st.header("📊 View Reports")
    
    # Get output directory
    try:
        output_dir = Path(st.session_state.config.get('output.local_dir', './outputs'))
    except:
        output_dir = Path('./outputs')
    
    if not output_dir.exists():
        st.warning("⚠️ No reports directory found. Run a verification first!")
        return
    
    # List available reports
    report_dirs = [d for d in output_dir.iterdir() if d.is_dir() and (d / 'report.json').exists()]
    
    if not report_dirs:
        st.info("📭 No reports found yet. Complete a verification to generate reports.")
        return
    
    # Sort by modification time (most recent first)
    report_dirs = sorted(report_dirs, key=lambda x: x.stat().st_mtime, reverse=True)
    
    # Report selector
    st.subheader("📋 Select Report")
    
    # Create options dict
    report_options = {}
    for report_dir in report_dirs:
        video_id = report_dir.name
        report = load_report(video_id, output_dir)
        if report:
            title = report.get('title', video_id)
            report_options[f"{title} ({video_id})"] = video_id
    
    if not report_options:
        st.warning("No valid reports found.")
        return
    
    # Dropdown selector
    selected_option = st.selectbox(
        "Choose a report:",
        options=list(report_options.keys()),
        index=0
    )
    
    selected_video_id = report_options[selected_option]
    
    # Load selected report
    report = load_report(selected_video_id, output_dir)
    
    if not report:
        st.error("Failed to load report.")
        return
    
    st.markdown("---")
    
    # Report header
    st.subheader(f"🎥 {report.get('title', 'Video Report')}")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        truth_score = report.get('overall_truthfulness_score', 0)
        if truth_score >= 0.7:
            st.metric("Truthfulness", f"{truth_score:.1%}", delta="High", delta_color="normal")
        elif truth_score >= 0.4:
            st.metric("Truthfulness", f"{truth_score:.1%}", delta="Mixed", delta_color="off")
        else:
            st.metric("Truthfulness", f"{truth_score:.1%}", delta="Low", delta_color="inverse")
    
    with col2:
        claims_count = len(report.get('verified_claims', []))
        st.metric("Claims Verified", claims_count)
    
    with col3:
        true_claims = sum(1 for c in report.get('verified_claims', []) 
                         if c.get('probability_distribution', {}).get('TRUE', 0) > 0.5)
        st.metric("True Claims", true_claims)
    
    with col4:
        false_claims = sum(1 for c in report.get('verified_claims', []) 
                          if c.get('probability_distribution', {}).get('FALSE', 0) > 0.5)
        st.metric("False Claims", false_claims)
    
    st.markdown("---")
    
    # Video embed
    if report.get('youtube_url'):
        st.subheader("📹 Original Video")
        st.video(report['youtube_url'])
    
    st.markdown("---")
    
    # Tab view for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Claims", "📊 Summary", "📄 Raw JSON", "💾 Download"])
    
    with tab1:
        st.subheader("Verified Claims")
        claims = report.get('verified_claims', [])
        render_claims_table(claims)
    
    with tab2:
        st.subheader("Executive Summary")
        
        # Overall assessment
        st.markdown("### Overall Assessment")
        summary_text = report.get('summary', 'No summary available.')
        st.write(summary_text)
        
        # Key findings
        st.markdown("### Key Findings")
        
        true_claims = [c for c in report.get('verified_claims', []) 
                      if c.get('probability_distribution', {}).get('TRUE', 0) > 0.5]
        false_claims = [c for c in report.get('verified_claims', []) 
                       if c.get('probability_distribution', {}).get('FALSE', 0) > 0.5]
        uncertain_claims = [c for c in report.get('verified_claims', []) 
                           if c.get('probability_distribution', {}).get('UNCERTAIN', 0) > 0.5]
        
        if true_claims:
            with st.expander(f"✅ True Claims ({len(true_claims)})"):
                for claim in true_claims[:5]:
                    st.markdown(f"- {claim.get('claim_text', 'N/A')}")
        
        if false_claims:
            with st.expander(f"❌ False Claims ({len(false_claims)})"):
                for claim in false_claims[:5]:
                    st.markdown(f"- {claim.get('claim_text', 'N/A')}")
        
        if uncertain_claims:
            with st.expander(f"❓ Uncertain Claims ({len(uncertain_claims)})"):
                for claim in uncertain_claims[:5]:
                    st.markdown(f"- {claim.get('claim_text', 'N/A')}")
        
        # Visualization
        st.markdown("### Claims Distribution")
        
        import pandas as pd
        dist_data = pd.DataFrame({
            'Category': ['True', 'False', 'Uncertain'],
            'Count': [len(true_claims), len(false_claims), len(uncertain_claims)]
        })
        
        st.bar_chart(dist_data.set_index('Category'))
    
    with tab3:
        st.subheader("Raw JSON Report")
        st.json(report)
    
    with tab4:
        st.subheader("Download Reports")
        
        report_dir = output_dir / selected_video_id
        
        # JSON download
        col_d1, col_d2, col_d3 = st.columns(3)
        
        with col_d1:
            json_path = report_dir / 'report.json'
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_content = f.read()
                
                st.download_button(
                    "📄 Download JSON",
                    json_content,
                    file_name=f"{selected_video_id}_report.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col_d2:
            md_path = report_dir / 'report.md'
            if md_path.exists():
                with open(md_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                
                st.download_button(
                    "📝 Download Markdown",
                    md_content,
                    file_name=f"{selected_video_id}_report.md",
                    mime="text/markdown",
                    use_container_width=True
                )
        
        with col_d3:
            html_path = report_dir / 'report.html'
            if html_path.exists():
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                st.download_button(
                    "🌐 Download HTML",
                    html_content,
                    file_name=f"{selected_video_id}_report.html",
                    mime="text/html",
                    use_container_width=True
                )
        
        # Preview HTML report
        if html_path.exists():
            st.markdown("---")
            st.subheader("HTML Report Preview")
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Render HTML in iframe
            components.html(html_content, height=600, scrolling=True)
    
    # Delete report option
    st.markdown("---")
    with st.expander("🗑️ Danger Zone"):
        st.warning("**Delete this report?** This action cannot be undone.")
        
        col_del1, col_del2 = st.columns([1, 3])
        
        with col_del1:
            if st.button("Delete Report", type="secondary"):
                # Confirm deletion
                st.session_state.confirm_delete = selected_video_id
        
        if st.session_state.get('confirm_delete') == selected_video_id:
            st.error("Are you sure? Click again to confirm.")
            if st.button("⚠️ Yes, Delete Permanently"):
                import shutil
                try:
                    shutil.rmtree(output_dir / selected_video_id)
                    st.success("Report deleted successfully!")
                    del st.session_state.confirm_delete
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete report: {e}")


