"""
Gallery Tab Component

Browse and submit example verifications to the community gallery.
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime


def render_gallery_tab():
    """Render the example gallery tab."""
    
    st.header("🖼️ Example Gallery")
    
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
        search_query = st.text_input("🔍 Search examples:", placeholder="Enter keywords...")
    
    with col2:
        sort_by = st.selectbox("Sort by:", ["Most Recent", "Highest Score", "Lowest Score", "Most Claims"])
    
    with col3:
        truthfulness_filter = st.selectbox(
            "Truth Filter:",
            ["All", "High (>70%)", "Medium (40-70%)", "Low (<40%)"]
        )
    
    st.markdown("---")
    
    # Load actual gallery items from gallery/ directory
    st.subheader("📚 Examples")
    
    # Try to load from gallery/approved/ directory
    import os
    gallery_dir = Path('./ui/gallery/approved')
    examples = []
    
    if gallery_dir.exists():
        for item in gallery_dir.iterdir():
            if item.is_file() and item.suffix == '.json':
                try:
                    with open(item, 'r') as f:
                        example = json.load(f)
                        examples.append(example)
                except:
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
        filtered_examples = sorted(filtered_examples, key=lambda x: x['submitted_at'], reverse=True)
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
                        # Show video embed instead of thumbnail
                        st.video(example['youtube_url'])
                        
                        st.markdown(f"**{example['title']}**")
                        st.caption(f"{example['category']}")
                        
                        # Metrics
                        met_col1, met_col2 = st.columns(2)
                        
                        with met_col1:
                            score = example['truthfulness_score']
                            color = "🟢" if score > 0.7 else "🟡" if score > 0.4 else "🔴"
                            st.metric("Truth", f"{color} {score:.0%}")
                        
                        with met_col2:
                            st.metric("Claims", example['claims_count'])
                        
                        # Tags
                        tags_str = " ".join([f"`{tag}`" for tag in example['tags'][:3]])
                        st.markdown(tags_str)
                        
                        # View button
                        if st.button("View Report", key=f"view_{example['id']}", use_container_width=True):
                            st.info(f"Loading report for: {example['title']}")
                            # In production, load actual report
                        
                        # Metadata
                        st.caption(f"By {example['submitted_by']} • {example['submitted_at']}")
                        
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

