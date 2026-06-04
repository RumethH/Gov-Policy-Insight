import streamlit as st


def render_header() -> None:
    st.markdown(
        """
        <div style="text-align: center;">
            <h1 style="margin-bottom: 0;">ChatGPI</h1>
            <p style="opacity: 0.8; margin-top: 0;">Policy Intelligence Assistant</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
