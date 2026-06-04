from typing import Optional

import streamlit as st


def render_composer(disabled: bool = False) -> Optional[str]:
    prompt = st.chat_input(
        placeholder="Ask about government policies...",
        key="pending_input",
        disabled=disabled,
    )
    return prompt
