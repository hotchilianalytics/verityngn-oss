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

    # Get output directory
    try:
        output_dir = Path(st.session_state.config.get("output.local_dir", "./outputs"))
    except (AttributeError, KeyError):
        output_dir = Path("./outputs")

    if not output_dir.exists():
        st.warning("⚠️ No reports directory found. Run a verification first!")
        return

    # List available reports
    report_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
    report_files = [
        d / "report.json" for d in report_dirs if (d / "report.json").exists()
    ]

    if not report_files:
        st.info("📭 No reports found yet. Complete a verification to generate reports.")
        return

    # Sort by modification time
    report_files = sorted(report_files, key=lambda x: x.stat().st_mtime, reverse=True)

    # Report selector
    st.subheader("📋 Select Report")

    report_options = {}
    for report_file in report_files:
        with open(report_file, "r") as f:
            report = json.load(f)
        video_id = report.get("video_id", report_file.parent.name)
        title = report.get("title", video_id)
        report_options[f"{title} ({video_id})"] = report_file

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

    # Enhanced key metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        truth_score = report.get("overall_truthfulness_score", 0)
        if truth_score >= 0.7:
            st.metric("Truthfulness", f"{truth_score:.1%}", delta="✅ High")
        elif truth_score >= 0.4:
            st.metric("Truthfulness", f"{truth_score:.1%}", delta="⚠️ Mixed")
        else:
            st.metric("Truthfulness", f"{truth_score:.1%}", delta="❌ Low")

    with col2:
        claims = report.get("verified_claims", []) or report.get("claims", [])
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

    verdict = report.get(
        "verdict", report.get("quick_summary", {}).get("verdict", "Unknown")
    )
    explanation = report.get(
        "explanation",
        report.get("quick_summary", {}).get("summary", "No explanation available"),
    )

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
