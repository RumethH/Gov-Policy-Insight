from datetime import datetime
from typing import Optional

import streamlit as st


from utils.state import switch_chat

def render_sidebar() -> Optional[str]:
    action = None
    st.title("ChatGPI")
    st.caption("Policy Intelligence Workspace")

    if st.button("New Chat", use_container_width=True, type="primary"):
        action = "new_chat"

    st.subheader("Conversations")
    if not st.session_state.history:
        st.info("No saved conversations yet.")
    else:
        for item in st.session_state.history:
            if st.button(item["title"], key=f"hist_{item['id']}", use_container_width=True):
                switch_chat(item["id"])
                st.rerun()


    st.divider()
    st.subheader("Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Mode", st.session_state.service_mode)
    with col2:
        st.metric("Updated", datetime.now().strftime("%H:%M"))

    st.info(f"Model: {st.session_state.model_status}")

    with st.expander("Settings"):
        service_mode = st.selectbox(
            "Response Source",
            options=["mock", "local_rag", "api"],
            index=["mock", "local_rag", "api"].index(st.session_state.service_mode),
        )
        if service_mode != st.session_state.service_mode:
            st.session_state.service_mode = service_mode
            st.session_state.model_status = {
                "mock": "Mock Assistant",
                "local_rag": "Local RAG Chain",
                "api": "FastAPI Backend",
            }[service_mode]
            st.rerun()

        st.divider()
        st.markdown("**Google Gemini API Key** *(optional)*")
        st.caption("Provide your own key if the demo quota is exceeded.")
        user_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.get("guest_api_key", ""),
            type="password",
            placeholder="AIza...",
            label_visibility="collapsed",
        )
        if user_key != st.session_state.get("guest_api_key", ""):
            st.session_state.guest_api_key = user_key
            if user_key:
                st.success("Key saved for this session.")

        st.divider()
        if st.button("Clear Conversation", use_container_width=True):
            action = "new_chat"

    return action
