import streamlit as st


def render_loading_state(message: str) -> None:
    """Render a standard Streamlit spinner for loading."""
    with st.spinner(message):
        # The spinner is context-managed; this function is called in a loop in app.py
        # but the spinner itself will be handled by the empty slot in app.py
        st.markdown(f"*{message}*")
