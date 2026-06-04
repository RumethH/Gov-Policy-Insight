from typing import Any, Dict, List

import streamlit as st


def _render_citations(citations: List[Dict[str, Any]]) -> None:
    if not citations:
        return

    with st.expander("Sources", expanded=False):
        for citation in citations:
            source = citation.get("source", "Unknown source")
            page = citation.get("page", "N/A")
            st.markdown(f"- **{source}** (page {page})")


def render_chat_thread(messages: List[Dict[str, Any]]) -> None:
    if not messages:
        st.info("Ask anything about government policies to get started.")
        st.caption("Try: 'Summarize the key compliance obligations in the NSW cyber policy.'")
    else:
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                _render_citations(msg.get("citations", []))
