"""
Navigation helpers for the single-page Streamlit app.

The app uses a sidebar radio (st.session_state.nav_selection) to choose which
tab/page to render. These helpers provide a consistent way to jump to Gallery
and (optionally) prefill the Gallery search box.
"""

from typing import Optional


GALLERY_TAB_LABEL = "🖼️ Gallery"


def go_to_gallery(video_id: Optional[str] = None) -> None:
    """Navigate to Gallery and optionally prefill search with a video_id."""
    try:
        import streamlit as st

        st.session_state.nav_selection = GALLERY_TAB_LABEL
        if video_id:
            st.session_state.gallery_search_query = video_id
        st.rerun()
    except Exception:
        return


def render_gallery_cta(*, key: str, video_id: Optional[str] = None) -> None:
    """
    Render a small call-to-action pointing users to Gallery for reports.
    """
    import streamlit as st

    col_msg, col_btn = st.columns([5, 2])
    with col_msg:
        st.info("Reports are saved to the **🖼️ Gallery**. Open Gallery to view them.")
    with col_btn:
        if st.button("🖼️ Open Gallery", key=key, use_container_width=True):
            go_to_gallery(video_id=video_id)


