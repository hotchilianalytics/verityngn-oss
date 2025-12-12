import os
from typing import Optional


def ui_debug_enabled() -> bool:
    """
    Return True if UI debug output should be shown.

    Priority:
    1) Environment variable VERITYNGN_UI_DEBUG
    2) Streamlit session state key 'ui_debug'
    """
    env_flag = os.getenv("VERITYNGN_UI_DEBUG", "").strip().lower()
    if env_flag in ("1", "true", "yes", "y", "on"):
        return True

    try:
        import streamlit as st

        return bool(st.session_state.get("ui_debug", False))
    except Exception:
        return False


def debug_write(message: str) -> None:
    """Write a debug message to the Streamlit UI only when debug is enabled."""
    if not ui_debug_enabled():
        return
    try:
        import streamlit as st

        st.write(message)
    except Exception:
        # If Streamlit isn't available (e.g., non-UI context), do nothing
        return


def debug_exception(title: str, exc: BaseException) -> None:
    """
    Show a traceback in the Streamlit UI only when debug is enabled.
    Always safe: does not print secrets directly.
    """
    if not ui_debug_enabled():
        return

    try:
        import streamlit as st
        import traceback

        st.error(title)
        with st.expander("Error details (debug)"):
            st.code(traceback.format_exc())
    except Exception:
        return


