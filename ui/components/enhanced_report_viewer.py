"""
Enhanced Report Viewer for Public Release

Displays claim quality scores, absence claims, and transcript analysis.
"""

import streamlit as st
import json
from pathlib import Path


def render_claim_quality_badge(specificity: int, verifiability: float, claim_type: str):
    """Render a visual quality badge for a claim."""
    # Determine quality level
    if specificity >= 70 and verifiability >= 0.8:
        quality = "EXCELLENT"
        color = "#28a745"  # Green
        emoji = "🌟"
    elif specificity >= 50 and verifiability >= 0.6:
        quality = "GOOD"
        color = "#17a2b8"  # Blue
        emoji = "✅"
    elif specificity >= 40 and verifiability >= 0.5:
        quality = "ACCEPTABLE"
        color = "#ffc107"  # Yellow
        emoji = "👍"
    elif specificity >= 30 or verifiability >= 0.4:
        quality = "WEAK"
        color = "#fd7e14"  # Orange
        emoji = "⚠️"
    else:
        quality = "POOR"
        color = "#dc3545"  # Red
        emoji = "❌"

    st.markdown(
        f"""
    <div style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 0.5rem; 
                background-color: {color}20; border: 2px solid {color}; 
                color: {color}; font-weight: bold; margin-right: 0.5rem;">
        {emoji} {quality}
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Show scores inline
    st.caption(
        f"📊 Specificity: {specificity}/100 | Verifiability: {verifiability:.2f}"
    )

    # Show claim type
    type_emojis = {
        "absence": "🚫",
        "credential": "🎓",
        "publication": "📰",
        "study": "🔬",
        "product_efficacy": "💊",
        "celebrity": "⭐",
        "conspiracy": "🕵️",
        "other": "📌",
    }
    emoji = type_emojis.get(claim_type, "📌")
    st.caption(f"{emoji} Type: **{claim_type.replace('_', ' ').title()}**")


def render_absence_claims_section(claims: list):
    """Render absence claims in a highlighted section."""
    absence_claims = [c for c in claims if c.get("claim_type") == "absence"]

    if not absence_claims:
        return

    st.markdown("---")
    st.markdown("## 🚫 Missing Information (Absence Claims)")
    st.markdown(
        """
    <div style="background-color: #fff3cd; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ffc107; margin-bottom: 1rem;">
        <strong>⚠️ High-Value Findings:</strong> These claims identify information that is <strong>NOT stated</strong> 
        in the video. Missing credentials, sources, or verification details are often strong indicators of 
        misinformation or fraud.
    </div>
    """,
        unsafe_allow_html=True,
    )

    for i, claim in enumerate(absence_claims, 1):
        with st.expander(
            f"🚫 **Absence Claim {i}:** {claim.get('claim_text', 'N/A')[:80]}..."
        ):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**What's Missing:** {claim.get('claim_text', 'N/A')}")
                st.markdown(
                    f"**Why It Matters:** {claim.get('initial_assessment', 'Missing verification details can indicate fraud')}"
                )

            with col2:
                # Quality scores
                render_claim_quality_badge(
                    specificity=claim.get("specificity_score", 85),
                    verifiability=claim.get("verifiability_score", 0.9),
                    claim_type=claim.get("claim_type", "absence"),
                )


def render_transcript_analysis_section(ci_data: list):
    """Render YouTube counter-intelligence with transcript analysis."""
    # Filter videos that have transcript analysis
    analyzed_videos = [v for v in ci_data if v.get("has_transcript_analysis")]

    if not analyzed_videos:
        return

    st.markdown("---")
    st.markdown("## 📝 Counter-Evidence from Video Transcripts")
    st.markdown(
        """
    <div style="background-color: #d1ecf1; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #17a2b8; margin-bottom: 1rem;">
        <strong>🎯 Deep Analysis:</strong> We analyzed transcripts from debunking/review videos to extract 
        specific counter-claims with evidence.
    </div>
    """,
        unsafe_allow_html=True,
    )

    for video in analyzed_videos:
        title = video.get("title", "Counter-Evidence Video")
        transcript_analysis = video.get("transcript_analysis", {})
        counter_claims = transcript_analysis.get("counter_claims", [])

        if not counter_claims:
            continue

        with st.expander(f"📺 **{title}**"):
            # Video metadata
            st.markdown(
                f"**Video:** [{title}](https://www.youtube.com/watch?v={video.get('id', '')})"
            )
            st.markdown(f"**Views:** {video.get('view_count', 0):,}")

            # Counter-claims
            st.markdown("### 🎯 Counter-Claims Extracted:")

            for i, counter_claim in enumerate(counter_claims, 1):
                claim_text = counter_claim.get("claim_text", "N/A")
                evidence_snippet = counter_claim.get("evidence_snippet", "")
                credibility = counter_claim.get("credibility_score", 0)
                claim_type = counter_claim.get("claim_type", "other")

                # Credibility indicator
                if credibility >= 0.8:
                    cred_icon = "🟢"
                    cred_label = "High Credibility"
                elif credibility >= 0.6:
                    cred_icon = "🟡"
                    cred_label = "Medium Credibility"
                else:
                    cred_icon = "🔴"
                    cred_label = "Low Credibility"

                st.markdown(
                    f"""
                **{i}. {claim_text}**
                
                {cred_icon} *{cred_label}* ({credibility:.0%}) | Type: *{claim_type.replace('_', ' ').title()}*
                
                > 💬 "{evidence_snippet[:200]}{'...' if len(evidence_snippet) > 200 else ''}"
                """
                )

                st.markdown("---")


def render_enhanced_claims_table(claims: list):
    """Render claims with enhanced quality information."""
    if not claims:
        st.info("No claims found in this report.")
        return

    # Separate absence claims from regular claims
    regular_claims = [c for c in claims if c.get("claim_type") != "absence"]
    absence_claims = [c for c in claims if c.get("claim_type") == "absence"]

    # Show regular claims
    st.markdown("## 📋 Verified Claims")

    # Add filter options
    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        quality_filter = st.multiselect(
            "Filter by Quality",
            options=["EXCELLENT", "GOOD", "ACCEPTABLE", "WEAK", "POOR"],
            default=["EXCELLENT", "GOOD", "ACCEPTABLE"],
        )

    with filter_col2:
        type_filter = st.multiselect(
            "Filter by Type",
            options=["credential", "publication", "study", "product_efficacy", "other"],
            default=["credential", "publication", "study", "product_efficacy", "other"],
        )

    # Apply filters
    filtered_claims = regular_claims
    if "quality_level" in (claims[0] if claims else {}):
        filtered_claims = [
            c
            for c in regular_claims
            if c.get("quality_level", "UNKNOWN") in quality_filter
            and c.get("claim_type", "other") in type_filter
        ]

    st.caption(f"Showing {len(filtered_claims)} of {len(regular_claims)} claims")

    for i, claim in enumerate(filtered_claims, 1):
        with st.expander(f"**Claim {i}:** {claim.get('claim_text', 'N/A')[:100]}..."):
            # Top row: Quality badge and metrics
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                # Quality badge
                if "specificity_score" in claim:
                    render_claim_quality_badge(
                        specificity=claim.get("specificity_score", 0),
                        verifiability=claim.get("verifiability_score", 0),
                        claim_type=claim.get("claim_type", "other"),
                    )

            with col2:
                # Probability distribution
                prob_dist = claim.get("probability_distribution", {})
                if prob_dist:
                    max_outcome = max(prob_dist, key=prob_dist.get)
                    max_prob = prob_dist[max_outcome]

                    if max_outcome == "TRUE" or max_outcome == "HIGHLY_LIKELY_TRUE":
                        st.metric("Verdict", "✅ TRUE", f"{max_prob:.0%}")
                    elif max_outcome == "FALSE" or max_outcome == "LIKELY_FALSE":
                        st.metric("Verdict", "❌ FALSE", f"{max_prob:.0%}")
                    else:
                        st.metric("Verdict", "❓ UNCERTAIN", f"{max_prob:.0%}")

            with col3:
                sources = claim.get("sources", [])
                st.metric("Sources", len(sources))

            # Claim content
            st.markdown("---")
            st.markdown(f"**Full Claim:** {claim.get('claim_text', 'N/A')}")

            # Timestamp and speaker
            if claim.get("timestamp"):
                st.caption(
                    f"🕒 Timestamp: {claim['timestamp']} | 🗣️ Speaker: {claim.get('speaker', 'Unknown')}"
                )

            # Evidence summary
            st.markdown("**Evidence Summary:**")
            st.write(claim.get("evidence_summary", "No summary available"))

            # Show probability details
            if prob_dist:
                st.markdown("**Probability Distribution:**")
                prob_col1, prob_col2, prob_col3 = st.columns(3)

                with prob_col1:
                    st.metric(
                        "TRUE",
                        f"{prob_dist.get('TRUE', prob_dist.get('HIGHLY_LIKELY_TRUE', 0)):.1%}",
                    )
                with prob_col2:
                    st.metric("UNCERTAIN", f"{prob_dist.get('UNCERTAIN', 0):.1%}")
                with prob_col3:
                    st.metric(
                        "FALSE",
                        f"{prob_dist.get('FALSE', prob_dist.get('LIKELY_FALSE', 0)):.1%}",
                    )

            # Sources
            if sources:
                with st.expander(f"📚 View {len(sources)} Source(s)"):
                    for j, source in enumerate(sources, 1):
                        st.markdown(
                            f"{j}. [{source.get('title', 'Source')}]({source.get('url', '#')})"
                        )
                        if source.get("snippet"):
                            st.caption(f"> {source['snippet'][:200]}...")

    # Show absence claims separately
    if absence_claims:
        render_absence_claims_section(absence_claims)


def render_enhanced_report_viewer_tab():
    """Enhanced report viewer with quality scores and transcript analysis."""

    st.header("📊 View Enhanced Reports")

    # 🎯 STREAMLIT CLOUD FIX: Check if API mode is enabled (Streamlit Cloud)
    import os
    API_MODE = os.getenv("VERITYNGN_API_URL") is not None
    
    if API_MODE:
        # Use API-based report retrieval for Streamlit Cloud
        try:
            import sys
            # Ensure ui directory is in path
            ui_dir = Path(__file__).parent.parent
            if str(ui_dir) not in sys.path:
                sys.path.insert(0, str(ui_dir))
            from api_client import get_default_client
            api_client = get_default_client()
            
            st.info("🌐 Using API mode - reports will be fetched from the API")
            
            # For now, show a message that API-based report listing is coming soon
            # Users can view reports via the processing tab after completion
            st.warning("⚠️ Report viewer in API mode: View reports from the 'Process Video' tab after verification completes.")
            st.info("💡 Tip: After submitting a verification, use the 'View Report' buttons in the processing tab.")
            return
            
        except Exception as e:
            st.error(f"❌ Error initializing API client: {e}")
            return

    # 🎯 FIXED: Use same logic as simplified report_viewer.py
    # Find outputs directory (where reports actually are)
    # Priority: /app/outputs (Docker mount) > outputs (local) > outputs_debug (legacy)
    possible_dirs = [
        Path('/app/outputs'),  # Docker mount point (highest priority)
        Path.cwd() / 'outputs',  # Standard outputs directory
        Path.cwd() / 'verityngn' / 'outputs_debug',  # Legacy location
        Path.cwd() / 'outputs_debug',  # Legacy alternative
        Path(__file__).parent.parent.parent / 'verityngn' / 'outputs_debug',  # Relative to this file
        Path(__file__).parent.parent / 'outputs',  # From UI directory
    ]
    
    output_dir = None
    for dir_path in possible_dirs:
        try:
            if dir_path.exists():
                output_dir = dir_path
                print(f"✅ Found output directory: {output_dir.absolute()}")
                break
        except (PermissionError, OSError) as e:
            # Skip directories we don't have permission to access (e.g., Streamlit Cloud)
            continue
    
    # Fallback to config if not found
    if not output_dir:
        try:
            output_dir = Path(
                st.session_state.config.get("output.local_dir", "./outputs")
            )
        except (AttributeError, KeyError):
            output_dir = Path("./outputs")

    # Check if output_dir exists (with error handling)
    try:
        dir_exists = output_dir.exists()
    except (PermissionError, OSError):
        dir_exists = False

    if not output_dir or not dir_exists:
        st.warning("⚠️ No reports directory found. Run a verification first!")
        with st.expander("🔍 Debug Info"):
            st.info("Searched in:\n" + "\n".join([f"- {d}" for d in possible_dirs]))
        return

    # 🎯 FIXED: List available reports from timestamped _complete directories
    report_files = []
    
    # 1. Scan standard output directory
    if output_dir and output_dir.exists():
        try:
            for video_dir in output_dir.iterdir():
                try:
                    if not video_dir.is_dir():
                        continue
                except (PermissionError, OSError):
                    continue
                
                video_id = video_dir.name
                
                # Look for reports in timestamped _complete directories
                try:
                    complete_dirs = sorted(
                        [d for d in video_dir.glob('*_complete') if d.is_dir()],
                        key=lambda x: x.stat().st_mtime,
                        reverse=True  # Most recent first
                    )
                except (PermissionError, OSError):
                    continue
                
                for complete_dir in complete_dirs:
                    # Try both naming conventions
                    report_paths = [
                        complete_dir / f'{video_id}_report.json',
                        complete_dir / 'report.json',
                    ]
                    
                    for report_path in report_paths:
                        try:
                            if report_path.exists():
                                report_files.append(report_path)
                                break
                        except (PermissionError, OSError):
                            continue
                    
                    if report_files and report_files[-1].parent == complete_dir:
                        break  # Found report in this video_dir, move to next
        except (PermissionError, OSError) as e:
            st.error(f"❌ Permission error accessing reports directory: {e}")
            st.info("💡 In Streamlit Cloud, use API mode to view reports via the API.")

    # 2. Scan for local Sherlock analysis folders (development/debug artifacts)
    try:
        for sherlock_dir in Path.cwd().glob('sherlock_analysis_*'):
            if not sherlock_dir.is_dir():
                continue
            
            video_id = sherlock_dir.name.replace('sherlock_analysis_', '')
            
            # Priority: report.json > final_claims.json
            candidates = [
                sherlock_dir / f"{video_id}_report.json",
                sherlock_dir / "report.json",
                sherlock_dir / f"{video_id}_final_claims.json"
            ]
            
            for cand in candidates:
                if cand.exists():
                    report_files.append(cand)
                    break
    except Exception as e:
        print(f"Warning scanning sherlock dirs: {e}")

    if not report_files:
        st.info("📭 No reports found yet. Complete a verification to generate reports.")
        st.info(f"📂 Looking in: {output_dir.absolute()}")
        return

    # Sort by modification time (with error handling)
    try:
        report_files = sorted(report_files, key=lambda x: x.stat().st_mtime, reverse=True)
    except (PermissionError, OSError):
        # If we can't get modification times, just use the order we found them
        pass

    # Report selector
    st.subheader("📋 Select Report")

    if not report_files:
        st.info("📭 No reports found yet. Complete a verification to generate reports.")
        st.info(f"📂 Looking in: {output_dir.absolute()}")
        return

    report_options = {}
    for report_file in report_files:
        try:
            with open(report_file, "r") as f:
                report = json.load(f)
            video_id = report.get("video_id", report_file.parent.name)
            title = report.get("title", video_id)
            # Include timestamp in label for clarity
            timestamp = report.get("timestamp", "")
            if not timestamp:
                # Try to get from directory name
                try:
                    dir_name = report_file.parent.name
                    if "_complete" in dir_name:
                        timestamp = dir_name.split("_complete")[0]
                except Exception:
                    pass
            
            label = f"{title} ({video_id})"
            if timestamp:
                label += f" - {timestamp}"
                
            report_options[label] = report_file
        except Exception as e:
            print(f"Error loading report {report_file}: {e}")
            continue

    if not report_options:
        st.warning("Found report files but failed to load them. Check console logs.")
        return

    selected_option = st.selectbox(
        "Choose a report:", options=list(report_options.keys()), index=0
    )

    selected_report_file = report_options[selected_option]

    # Load report
    with open(selected_report_file, "r") as f:
        report = json.load(f)

    st.markdown("---")

    # Report header
    st.subheader(f"🎥 {report.get('title', 'Video Report')}")

    # 🔍 SHERLOCK FIX: Extract claims from correct key
    # Old format: 'verified_claims' or 'claims'
    # New format: 'claims_breakdown'
    claims = (report.get("verified_claims", []) or 
              report.get("claims", []) or 
              report.get("claims_breakdown", []))
    
    # 🔍 SHERLOCK FIX: Extract truthfulness score
    # Old format: 'overall_truthfulness_score'
    # New format: parse from 'overall_assessment'
    truth_score = report.get("overall_truthfulness_score")
    
    if truth_score is None:
        # Try to extract from overall_assessment
        assessment = report.get('overall_assessment', [])
        if isinstance(assessment, list) and len(assessment) >= 2:
            # Parse percentage from text like "100.0% of claims appear false"
            assessment_text = assessment[1]
            if 'false' in assessment_text.lower() and '100.0%' in assessment_text:
                truth_score = 0.0  # All false
            elif 'false' in assessment_text.lower():
                truth_score = 0.25  # Mostly false
            elif 'true' in assessment_text.lower() and '100.0%' in assessment_text:
                truth_score = 1.0  # All true
            elif 'true' in assessment_text.lower():
                truth_score = 0.75  # Mostly true
            else:
                truth_score = 0.5  # Mixed
        else:
            truth_score = 0.0  # Default

    # Enhanced key metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if truth_score >= 0.7:
            st.metric("Truthfulness", f"{truth_score:.1%}", delta="✅ High")
        elif truth_score >= 0.4:
            st.metric("Truthfulness", f"{truth_score:.1%}", delta="⚠️ Mixed")
        else:
            st.metric("Truthfulness", f"{truth_score:.1%}", delta="❌ Low")

    with col2:
        st.metric("Total Claims", len(claims))

    with col3:
        absence_count = sum(1 for c in claims if c.get("claim_type") == "absence")
        st.metric("🚫 Absence Claims", absence_count)

    with col4:
        if claims and "specificity_score" in claims[0]:
            avg_spec = sum(c.get("specificity_score", 0) for c in claims) / len(claims)
            st.metric("Avg Specificity", f"{avg_spec:.0f}/100")
        else:
            st.metric("Avg Specificity", "N/A")

    with col5:
        if claims and "verifiability_score" in claims[0]:
            avg_verif = sum(c.get("verifiability_score", 0) for c in claims) / len(
                claims
            )
            st.metric("Avg Verifiability", f"{avg_verif:.2f}")
        else:
            st.metric("Avg Verifiability", "N/A")

    # Video info
    with st.expander("📹 Video Information"):
        st.write(f"**URL:** {report.get('video_url', 'N/A')}")
        st.write(f"**Video ID:** {report.get('video_id', 'N/A')}")
        st.write(f"**Analysis Date:** {report.get('timestamp', 'N/A')}")

    # Enhanced claims table
    render_enhanced_claims_table(claims)

    # Counter-intelligence with transcript analysis
    ci_data = report.get("counter_intelligence", []) or report.get("ci_once", [])
    if ci_data:
        render_transcript_analysis_section(ci_data)

    # Final verdict
    st.markdown("---")
    st.markdown("## 🎯 Final Verdict")

    # 🔍 SHERLOCK FIX: Extract verdict and explanation
    # Old format: 'verdict' and 'explanation' keys
    # New format: 'overall_assessment' array [status, description]
    verdict = report.get("verdict")
    explanation = report.get("explanation")
    
    if not verdict:
        # Try new format
        assessment = report.get('overall_assessment', [])
        if isinstance(assessment, list) and len(assessment) >= 2:
            verdict = assessment[0]  # e.g., "Likely to be False"
            explanation = assessment[1]  # Full description
        else:
            # Fallback to quick_summary
            quick_summary = report.get("quick_summary", {})
            verdict = quick_summary.get("verdict", "Unknown")
            explanation = quick_summary.get("summary", "No explanation available")

    if "false" in verdict.lower() or truth_score < 0.4:
        verdict_color = "#dc3545"
        verdict_icon = "❌"
    elif "true" in verdict.lower() and truth_score >= 0.7:
        verdict_color = "#28a745"
        verdict_icon = "✅"
    else:
        verdict_color = "#ffc107"
        verdict_icon = "⚠️"

    st.markdown(
        f"""
    <div style="background-color: {verdict_color}20; padding: 1.5rem; border-radius: 0.5rem; border-left: 4px solid {verdict_color};">
        <h3 style="color: {verdict_color}; margin-top: 0;">{verdict_icon} {verdict}</h3>
        <p>{explanation}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    
    # 🎯 USER REQUESTED: Display HTML Report (Fast Report by Default)
    st.markdown("---")
    st.markdown("## 📄 Report View")
    
    # Check for fast report first
    fast_html_path = selected_report_file.parent / f"{selected_report_file.parent.parent.name}_fast_report.html"
    full_html_path = selected_report_file.parent / f"{selected_report_file.parent.parent.name}_report.html"
    
    # Determine which report to show
    display_html_path = None
    display_type = "Full"
    
    if fast_html_path.exists():
        display_html_path = fast_html_path
        display_type = "Fast"
    elif full_html_path.exists():
        display_html_path = full_html_path
        display_type = "Full"
        
    # Allow toggling if both exist
    if fast_html_path.exists() and full_html_path.exists():
        col_view_opts, _ = st.columns([1, 3])
        with col_view_opts:
            view_mode = st.radio("View Mode", ["Fast Summary", "Full Detailed Report"], horizontal=True)
            if view_mode == "Full Detailed Report":
                display_html_path = full_html_path
                display_type = "Full"
            else:
                display_html_path = fast_html_path
                display_type = "Fast"

    if display_html_path and display_html_path.exists():
        try:
            import streamlit.components.v1 as components
            
            with open(display_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Display HTML in iframe
            height = 800 if display_type == "Fast" else 1200
            components.html(html_content, height=height, scrolling=True)
            
            st.markdown("---")
            
            # Download buttons
            col_dl1, col_dl2 = st.columns(2)
            
            with col_dl1:
                if full_html_path.exists():
                    with open(full_html_path, 'r', encoding='utf-8') as f:
                        full_content = f.read()
                    st.download_button(
                        label="📥 Download Full Detailed Report",
                        data=full_content,
                        file_name=full_html_path.name,
                        mime="text/html",
                        use_container_width=True
                    )
            
            with col_dl2:
                if fast_html_path.exists():
                    with open(fast_html_path, 'r', encoding='utf-8') as f:
                        fast_content = f.read()
                    st.download_button(
                        label="📥 Download Fast Summary",
                        data=fast_content,
                        file_name=fast_html_path.name,
                        mime="text/html",
                        use_container_width=True
                    )
            
        except Exception as e:
            st.error(f"❌ Error loading HTML report: {e}")
            st.info(f"Expected HTML at: {display_html_path}")
    else:
        st.warning("📄 HTML report not found.")
        if full_html_path.exists():
             st.info(f"Found Full Report at: {full_html_path}")
        if fast_html_path.exists():
             st.info(f"Found Fast Report at: {fast_html_path}")
        st.info("The enhanced JSON view above shows all available data.")
