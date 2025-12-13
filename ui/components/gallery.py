"""
Gallery Tab Component

Browse and submit example verifications to the community gallery.
"""

import streamlit as st
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from components.ui_debug import ui_debug_enabled


# Cache configuration
CACHE_TTL = 300  # 5 minutes default cache TTL


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _cached_get_gallery_list(api_url: str, limit: int = 200, offset: int = 0) -> Dict[str, Any]:
    """
    Cached wrapper for fetching gallery list from API.
    
    Args:
        api_url: Base API URL
        limit: Maximum number of videos to return
        offset: Number of videos to skip
        
    Returns:
        Gallery data dictionary
    """
    from api_client import VerityNgnAPIClient
    client = VerityNgnAPIClient(api_url=api_url)
    return client.get_gallery_list(limit=limit, offset=offset)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _cached_get_gallery_video(api_url: str, video_id: str) -> Dict[str, Any]:
    """
    Cached wrapper for fetching gallery video details.
    
    Args:
        api_url: Base API URL
        video_id: YouTube video ID
        
    Returns:
        Video metadata dictionary
    """
    from api_client import VerityNgnAPIClient
    client = VerityNgnAPIClient(api_url=api_url)
    return client.get_gallery_video(video_id)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _cached_fetch_html_report(full_url: str) -> str:
    """
    Cached wrapper for fetching HTML report content.
    
    Args:
        full_url: Full URL to the HTML report
        
    Returns:
        HTML content as string
    """
    response = requests.get(full_url, timeout=30)
    response.raise_for_status()
    return response.text


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _cached_get_report_data(api_url: str, video_id: str) -> Dict[str, Any]:
    """
    Cached wrapper for fetching report data.
    
    Args:
        api_url: Base API URL
        video_id: YouTube video ID
        
    Returns:
        Report data dictionary
    """
    from api_client import VerityNgnAPIClient
    client = VerityNgnAPIClient(api_url=api_url)
    return client.get_report_data(video_id)


def _get_api_base_url() -> str:
    """
    Get the API base URL from session state or environment variables.
    
    Returns:
        API base URL with scheme (https://...)
    """
    import os
    
    # Try to get from session state api_client first
    api_client = st.session_state.get('api_client')
    if api_client and hasattr(api_client, 'api_url') and api_client.api_url:
        api_url = api_client.api_url.rstrip('/')
        # Ensure it has a scheme
        if api_url and not api_url.startswith(('http://', 'https://')):
            api_url = f"https://{api_url}"
        return api_url
    
    # Fall back to environment variables
    api_url = os.getenv('CLOUDRUN_API_URL') or os.getenv('VERITYNGN_API_URL', '')
    if api_url:
        api_url = api_url.rstrip('/')
        # Ensure it has a scheme
        if api_url and not api_url.startswith(('http://', 'https://')):
            api_url = f"https://{api_url}"
        return api_url
    
    # Default fallback (shouldn't happen in Cloud Run mode)
    return ""


def render_gallery_tab():
    """Render the example gallery tab."""
    
    # Check backend mode
    backend_mode = st.session_state.get('backend_mode', 'local')
    
    # Header with refresh button - always show refresh button
    col_header, col_refresh = st.columns([4, 1])
    with col_header:
        st.header("🖼️ Example Gallery")
    with col_refresh:
        st.write("")  # Spacer for alignment
        if st.button("🔄 Refresh", help="Clear cache and reload gallery data", use_container_width=True, key="gallery_refresh_btn"):
            # Clear all gallery-related caches
            _cached_get_gallery_list.clear()
            _cached_get_gallery_video.clear()
            _cached_fetch_html_report.clear()
            _cached_get_report_data.clear()
            st.success("✅ Cache cleared!")
            st.rerun()
    
    # Show backend mode info
    if backend_mode == 'cloudrun':
        st.info("☁️ **Cloud Run Mode**: Gallery will display reports from GCS bucket. Results from batch jobs automatically flow to the gallery.")
    
    st.markdown("""
    Browse example video verifications from the community. These examples demonstrate
    the system's capabilities across different types of content.
    """)
    
    st.markdown("---")
    
    # Gallery categories
    st.subheader("📂 Categories")
    
    categories = [
        "🏥 Health & Medicine",
        "💰 Finance & Investment",
        "🛍️ Product Reviews",
        "🔬 Science & Technology",
        "🗳️ Politics & News",
        "🎓 Education",
        "🌍 Environment & Climate",
        "🎬 Entertainment & Media",
        "🎮 Gaming",
        "🍳 Cooking & Food",
        "✈️ Travel & Tourism",
        "📚 Tutorials & How-To",
        "💪 Fitness & Wellness",
        "🏠 Lifestyle & DIY",
        "🚗 Automotive",
        "⚽ Sports",
        "🎨 Arts & Creativity",
        "🐾 Pets & Animals",
        "🔧 Tech Reviews & Gadgets",
        "📱 Social Media & Influencers",
        "✨ All Categories"
    ]
    
    selected_category = st.selectbox("Filter by category:", categories, index=len(categories)-1)
    
    # Search and filters
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Search examples:",
            placeholder="Enter keywords...",
            key="gallery_search_query",
        )
    
    with col2:
        sort_by = st.selectbox("Sort by:", ["Most Recent", "Highest Score", "Lowest Score", "Most Claims"])
    
    with col3:
        truthfulness_filter = st.selectbox(
            "Truth Filter:",
            ["All", "High (>70%)", "Medium (40-70%)", "Low (<40%)"]
        )
    
    st.markdown("---")
    
    # Load actual gallery items from gallery/ directory or GCS
    st.subheader("📚 Examples")
    
    import os
    examples = []
    
    # Check backend mode and fetch accordingly
    if backend_mode == 'cloudrun':
        # Fetch from GCS via API
        try:
            import sys
            # Ensure ui directory is in path
            ui_dir = Path(__file__).parent.parent
            if str(ui_dir) not in sys.path:
                sys.path.insert(0, str(ui_dir))
            from api_client import get_default_client
            
            # Get API URL - ensure it's valid
            api_url = _get_api_base_url()
            if not api_url:
                st.error("❌ Cloud Run API URL not configured. Please set CLOUDRUN_API_URL environment variable.")
                st.stop()
            
            # Fetch gallery videos from API (cached)
            with st.spinner("Loading gallery from GCS..."):
                gallery_data = _cached_get_gallery_list(api_url, limit=200, offset=0)
                
                # Deduplicate by video_id - keep only latest version per video_id
                video_dict = {}  # video_id -> latest video data
                
                # Process API response into gallery format
                for video_data in gallery_data.get('videos', []):
                    video_id = video_data['video_id']
                    completed_at = video_data.get('completed_at', '')
                    
                    # Check if we already have this video_id or if this is a newer version
                    existing = video_dict.get(video_id)
                    if not existing or completed_at > existing.get('submitted_at', ''):
                        # Calculate truthfulness score percentage
                        truthfulness_score = video_data.get('truthfulness_score', 0.5)
                        
                        # Extract category
                        category = video_data.get('category', '✨ All Categories')
                        
                        video_entry = {
                            'id': video_id,
                            'video_id': video_id,
                            'title': video_data.get('title', 'Untitled'),
                            'youtube_url': video_data.get('youtube_url', ''),
                            'truthfulness_score': truthfulness_score,
                            'claims_count': video_data.get('claims_count', 0),
                            'category': category,
                            'tags': video_data.get('tags', []),
                            'submitted_at': completed_at,
                            'submitted_by': 'cloud_batch',
                            'html_url': video_data.get('html_url'),  # Proxy URL for full report
                            'fast_html_url': video_data.get('fast_html_url'), # Proxy URL for fast report
                            'json_url': video_data.get('json_url'),
                            'markdown_url': video_data.get('markdown_url'),
                            'gcs_path': video_data.get('gcs_path', ''),
                        }
                        video_dict[video_id] = video_entry
                
                # Convert dict values to list
                examples = list(video_dict.values())
                
                if examples:
                    st.success(f"✅ Loaded {len(examples)} videos from GCS")
                else:
                    st.info("📭 No videos found in gallery yet. Submit videos via batch processing to add them.")
                    
        except Exception as e:
            st.error(f"❌ Failed to load gallery from GCS: {e}")
            if ui_debug_enabled():
                import traceback
                with st.expander("Error Details (debug)"):
                    st.code(traceback.format_exc())
            # Fallback to empty list
            examples = []
    else:
        # Local mode: Load from gallery/approved/ directory
        gallery_dir = Path('./ui/gallery/approved')
        
        if gallery_dir.exists():
            for item in gallery_dir.iterdir():
                if item.is_file() and item.suffix == '.json':
                    try:
                        with open(item, 'r') as f:
                            example = json.load(f)
                            
                            # Extract fields from report structure
                            # Handle media_embed structure (from imported reports)
                            if 'media_embed' in example:
                                media = example['media_embed']
                                example['youtube_url'] = media.get('video_url', '')
                                example['video_id'] = media.get('video_id', '')
                                if not example.get('title'):
                                    example['title'] = media.get('title', 'Untitled')
                            
                            # Extract from test_metadata if present
                            if 'test_metadata' in example:
                                test_meta = example['test_metadata']
                                if not example.get('category'):
                                    example['category'] = test_meta.get('category', '✨ All Categories')
                                if not example.get('tags'):
                                    example['tags'] = test_meta.get('tags', [])
                            
                            # Calculate truthfulness_score from quick_summary or claims
                            if 'truthfulness_score' not in example or example['truthfulness_score'] == 0.0:
                                # Try to calculate from quick_summary verdict
                                quick_summary = example.get('quick_summary', {})
                                verdict = quick_summary.get('verdict', '').lower()
                                if 'false' in verdict:
                                    example['truthfulness_score'] = 0.2
                                elif 'true' in verdict and 'false' not in verdict:
                                    example['truthfulness_score'] = 0.8
                                elif 'mixed' in verdict:
                                    example['truthfulness_score'] = 0.5
                                else:
                                    # Calculate from claims if available
                                    claims = example.get('claims', [])
                                    if claims:
                                        true_count = sum(1 for c in claims if 'true' in c.get('verdict', '').lower() and 'false' not in c.get('verdict', '').lower())
                                        example['truthfulness_score'] = true_count / len(claims) if claims else 0.0
                            
                            # Get claims_count
                            if 'claims_count' not in example or example['claims_count'] == 0:
                                claims = example.get('claims', [])
                                example['claims_count'] = len(claims)
                            
                            # Ensure all required fields exist with defaults
                            example.setdefault('submitted_at', datetime.now().strftime('%Y-%m-%d'))
                            example.setdefault('submitted_by', 'anonymous')
                            example.setdefault('tags', [])
                            example.setdefault('truthfulness_score', 0.0)
                            example.setdefault('claims_count', 0)
                            example.setdefault('youtube_url', '')
                            example.setdefault('video_id', '')
                            example.setdefault('title', 'Untitled')
                            example.setdefault('category', '✨ All Categories')
                            example.setdefault('id', item.stem)
                            
                            # Skip if no youtube_url (can't display video)
                            if not example.get('youtube_url'):
                                continue
                            
                            examples.append(example)
                    except Exception as e:
                        # Skip invalid files but log error for debugging
                        import traceback
                        st.warning(f"⚠️ Error loading gallery item {item.name}: {str(e)}")
                        continue
    
    # Fallback to placeholder examples if no gallery items found
    if not examples:
        st.info("📭 No gallery items yet. Placeholder examples shown below.")
        examples = [
            {
                "id": "example1",
                "title": "Miracle Weight Loss Supplement Claims",
                "category": "🏥 Health & Medicine",
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "video_id": "dQw4w9WgXcQ",
            "truthfulness_score": 0.25,
            "claims_count": 18,
            "submitted_by": "researcher_123",
            "submitted_at": "2025-10-15",
            "tags": ["supplement", "weight-loss", "health-claims"]
        },
        {
            "id": "example2",
            "title": "Cryptocurrency Investment Strategy Analysis",
            "category": "💰 Finance & Investment",
            "youtube_url": "https://www.youtube.com/watch?v=example2",
            "video_id": "example2",
            "truthfulness_score": 0.55,
            "claims_count": 24,
            "submitted_by": "analyst_456",
            "submitted_at": "2025-10-14",
            "tags": ["crypto", "investment", "trading"]
        },
        {
            "id": "example3",
            "title": "Educational Science Video Verification",
            "category": "🔬 Science & Technology",
            "youtube_url": "https://www.youtube.com/watch?v=example3",
            "video_id": "example3",
            "truthfulness_score": 0.92,
            "claims_count": 31,
            "submitted_by": "educator_789",
            "submitted_at": "2025-10-13",
            "tags": ["science", "education", "physics"]
        }
    ]
    
    # Filter examples
    filtered_examples = examples
    
    if selected_category != "✨ All Categories":
        filtered_examples = [e for e in filtered_examples if e['category'] == selected_category]
    
    if search_query:
        query_lower = search_query.lower()
        filtered_examples = [
            e for e in filtered_examples
            if query_lower in e['title'].lower() or any(query_lower in tag for tag in e['tags'])
        ]
    
    if truthfulness_filter == "High (>70%)":
        filtered_examples = [e for e in filtered_examples if e['truthfulness_score'] > 0.7]
    elif truthfulness_filter == "Medium (40-70%)":
        filtered_examples = [e for e in filtered_examples if 0.4 <= e['truthfulness_score'] <= 0.7]
    elif truthfulness_filter == "Low (<40%)":
        filtered_examples = [e for e in filtered_examples if e['truthfulness_score'] < 0.4]
    
    # Sort examples
    if sort_by == "Most Recent":
        filtered_examples = sorted(
            filtered_examples, 
            key=lambda x: x.get('submitted_at', '1970-01-01'), 
            reverse=True
        )
    elif sort_by == "Highest Score":
        filtered_examples = sorted(filtered_examples, key=lambda x: x['truthfulness_score'], reverse=True)
    elif sort_by == "Lowest Score":
        filtered_examples = sorted(filtered_examples, key=lambda x: x['truthfulness_score'])
    elif sort_by == "Most Claims":
        filtered_examples = sorted(filtered_examples, key=lambda x: x['claims_count'], reverse=True)
    
    # Display examples in grid
    if not filtered_examples:
        st.info("No examples match your filters. Try adjusting your search criteria.")
    else:
        # Display in rows of 2
        for i in range(0, len(filtered_examples), 2):
            col_a, col_b = st.columns(2)
            
            for col, example in zip([col_a, col_b], filtered_examples[i:i+2]):
                with col:
                    # Card-like display
                    with st.container():
                        # Show video embed instead of thumbnail (with error handling)
                        youtube_url = example.get('youtube_url', '')
                        if youtube_url:
                            try:
                                st.video(youtube_url)
                            except Exception as e:
                                st.warning(f"Could not load video: {youtube_url}")
                        else:
                            st.info("No video URL available")
                        
                        st.markdown(f"**{example.get('title', 'Untitled')}**")
                        st.caption(f"{example.get('category', '✨ All Categories')}")
                        
                        # Metrics
                        met_col1, met_col2 = st.columns(2)
                        
                        with met_col1:
                            score = example.get('truthfulness_score', 0.0)
                            color = "🟢" if score > 0.7 else "🟡" if score > 0.4 else "🔴"
                            st.metric("Truth", f"{color} {score:.0%}")
                        
                        with met_col2:
                            st.metric("Claims", example.get('claims_count', 0))
                        
                        # Tags
                        tags = example.get('tags', [])
                        if tags:
                            tags_str = " ".join([f"`{tag}`" for tag in tags[:3]])
                            st.markdown(tags_str)
                        
                        # View Report button - display HTML report if available
                        example_id = example.get('id', 'unknown')
                        example_title = example.get('title', 'Untitled')
                        video_id = example.get('video_id', '')
                        
                        # Use session state to track which report is open
                        report_state_key = f"show_report_{example_id}"
                        
                        # Check for HTML report URL (GCS signed URL or local path)
                        html_url = example.get('html_url')
                        fast_html_url = example.get('fast_html_url')
                        
                        # Fallback: if fast_html_url is missing but html_url follows proxy pattern, derive it
                        if html_url and not fast_html_url and '/gallery/content/' in html_url and '/html' in html_url:
                            fast_html_url = html_url.replace('/html', '/fast_report')
                        
                        # If still no fast report, fall back to full report for view
                        view_url = fast_html_url if fast_html_url else html_url
                        
                        html_report_path = example.get('test_metadata', {}).get('html_report_path') if not html_url else None
                        
                        if view_url:
                            # GCS proxy URL - fetch and display
                            if st.button("📄 View Report", key=f"view_{example_id}", use_container_width=True):
                                st.session_state[report_state_key] = not st.session_state.get(report_state_key, False)
                            
                            # Show report if state is True - FULL PAGE DISPLAY
                            if st.session_state.get(report_state_key, False):
                                # Close button at top
                                col_close, col_title = st.columns([1, 10])
                                with col_close:
                                    if st.button("❌ Close", key=f"close_{example_id}", use_container_width=True):
                                        st.session_state[report_state_key] = False
                                        st.rerun()
                                with col_title:
                                    st.markdown(f"### 📄 Verity Report: {example_title}")
                                
                                st.markdown("---")
                                
                                # Fetch HTML from API proxy URL and display
                                try:
                                    import streamlit.components.v1 as components
                                    
                                    # Construct full URL if view_url is relative
                                    if view_url.startswith('/'):
                                        # Relative URL - prepend API base URL
                                        api_base_url = _get_api_base_url()
                                        if not api_base_url:
                                            raise ValueError("API base URL not configured. Cannot fetch report.")
                                        full_view_url = f"{api_base_url}{view_url}"
                                    else:
                                        # Already a full URL
                                        full_view_url = view_url
                                    
                                    # Validate URL has scheme before caching/fetching
                                    if not full_view_url.startswith(('http://', 'https://')):
                                        raise ValueError(f"Invalid URL format: {full_view_url}. URL must start with http:// or https://")
                                    
                                    # Fetch HTML content from API proxy URL (cached)
                                    # This will fetch the FAST report if available
                                    html_content = _cached_fetch_html_report(full_view_url)
                                    
                                    # Use full height and width - no clipping
                                    components.html(html_content, height=1200, scrolling=True, width=None)
                                    
                                    st.markdown("---")
                                    
                                    # Download button - Always try to download the FULL report (html_url)
                                    if html_url:
                                        # Construct full download URL
                                        if html_url.startswith('/'):
                                            api_base_url = _get_api_base_url()
                                            full_download_url = f"{api_base_url}{html_url}" if api_base_url else ""
                                        else:
                                            full_download_url = html_url
                                            
                                        if full_download_url:
                                            # Fetch full report content for download
                                            full_report_content = _cached_fetch_html_report(full_download_url)
                                            
                                            st.download_button(
                                                label="📥 Download Full Detailed Report",
                                                data=full_report_content,
                                                file_name=f"{video_id}_report.html",
                                                mime="text/html",
                                                use_container_width=True
                                            )
                                except Exception as e:
                                    st.error(f"Error loading HTML report from API: {e}")
                                    st.info(f"Report URL: {full_view_url[:100] if 'full_view_url' in locals() else view_url[:100]}...")
                                    if ui_debug_enabled():
                                        import traceback
                                        with st.expander("Error Details (debug)"):
                                            st.code(traceback.format_exc())
                                    
                                    # Fallback: provide direct link
                                    fallback_url = full_view_url if 'full_view_url' in locals() else view_url
                                    st.markdown(f"[📄 Open Report in New Tab]({fallback_url})")
                                    
                        elif html_report_path:
                            # Local file path - existing behavior
                            html_path = Path(html_report_path)
                            if html_path.exists():
                                # Toggle button
                                if st.button("📄 View Report", key=f"view_{example_id}", use_container_width=True):
                                    st.session_state[report_state_key] = not st.session_state.get(report_state_key, False)
                                
                                # Show report if state is True - FULL PAGE DISPLAY
                                if st.session_state.get(report_state_key, False):
                                    # Close button at top
                                    col_close, col_title = st.columns([1, 10])
                                    with col_close:
                                        if st.button("❌ Close", key=f"close_{example_id}", use_container_width=True):
                                            st.session_state[report_state_key] = False
                                            st.rerun()
                                    with col_title:
                                        st.markdown(f"### 📄 Full Report: {example_title}")
                                    
                                    st.markdown("---")
                                    
                                    # Display HTML in full page (no expander, use full width)
                                    try:
                                        import streamlit.components.v1 as components
                                        with open(html_path, 'r', encoding='utf-8') as f:
                                            html_content = f.read()
                                        
                                        # Use full height and width - no clipping
                                        components.html(html_content, height=1200, scrolling=True, width=None)
                                        
                                        st.markdown("---")
                                        
                                        # Download button
                                        st.download_button(
                                            label="📥 Download HTML Report",
                                            data=html_content,
                                            file_name=f"{video_id}_report.html",
                                            mime="text/html",
                                            use_container_width=True
                                        )
                                    except Exception as e:
                                        st.error(f"Error loading HTML report: {e}")
                                        st.info(f"Report path: {html_path}")
                                        if ui_debug_enabled():
                                            import traceback
                                            with st.expander("Error Details (debug)"):
                                                st.code(traceback.format_exc())
                            else:
                                st.button("View Report", key=f"view_{example_id}", use_container_width=True, disabled=True)
                                st.caption("Report file not found")
                        elif video_id:
                            # Fallback: try API endpoint
                            report_url = f"/api/v1/reports/{video_id}/report.html"
                            st.markdown(f"[📄 View Report via API]({report_url})")
                        else:
                            st.info("Report not available")
                        
                        # Metadata
                        submitted_by = example.get('submitted_by', 'anonymous')
                        submitted_at = example.get('submitted_at', 'Unknown')
                        st.caption(f"By {submitted_by} • {submitted_at}")
                        
                        st.markdown("---")
    
    # Submit to gallery section
    st.markdown("---")
    st.subheader("📤 Submit to Gallery")
    
    with st.expander("➕ Submit Your Verification"):
        st.markdown("""
        Share your verification with the community! Help build a comprehensive
        gallery of examples demonstrating the system's capabilities.
        """)
        
        # Submission form
        submit_video_id = st.text_input("Video ID", placeholder="Enter the video ID from your reports")
        
        submit_category = st.selectbox(
            "Category",
            [cat for cat in categories if cat != "✨ All Categories"]
        )
        
        submit_tags = st.text_input(
            "Tags (comma-separated)",
            placeholder="e.g., health, supplement, claims"
        )
        
        submit_description = st.text_area(
            "Description (optional)",
            placeholder="Brief description of what makes this example interesting..."
        )
        
        agree_terms = st.checkbox("I agree to share this report publicly under CC BY 4.0 license")
        
        col_submit1, col_submit2 = st.columns([1, 3])
        
        with col_submit1:
            if st.button("Submit to Gallery", type="primary", disabled=not agree_terms):
                if submit_video_id:
                    try:
                        from ui.components.gallery_moderation import submit_to_gallery
                        
                        # Parse tags
                        tags_list = [tag.strip() for tag in submit_tags.split(',') if tag.strip()]
                        
                        # Submit for moderation
                        submission_id = submit_to_gallery(
                            video_id=submit_video_id,
                            category=submit_category,
                            tags=tags_list,
                            description=submit_description,
                            submitted_by=st.session_state.get('username', 'anonymous')
                        )
                        
                        st.success(f"✅ Submission received! (ID: {submission_id})")
                        st.info("Your submission will be reviewed by moderators before appearing in the gallery.")
                    except FileNotFoundError:
                        st.error(f"❌ Report not found for video ID: {submit_video_id}")
                    except Exception as e:
                        st.error(f"❌ Submission failed: {e}")
                else:
                    st.error("Please enter a valid video ID")
    
    # Gallery statistics
    st.markdown("---")
    st.subheader("📊 Gallery Statistics")
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric("Total Examples", len(examples))
    
    with stat_col2:
        avg_score = sum(e['truthfulness_score'] for e in examples) / len(examples)
        st.metric("Avg Truthfulness", f"{avg_score:.0%}")
    
    with stat_col3:
        total_claims = sum(e['claims_count'] for e in examples)
        st.metric("Total Claims", total_claims)
    
    with stat_col4:
        st.metric("Contributors", "142")
    
    # Info box
    st.info("""
    **Gallery Guidelines:**
    - Examples are community-submitted and reviewed before publication
    - All reports are available under Creative Commons CC BY 4.0 license
    - Report issues or inappropriate content using the flag button
    - See CONTRIBUTING.md for detailed submission guidelines
    """)

