import uuid

import streamlit as st


def init_session_state() -> None:
    defaults = {
        "messages": [],
        "history": [],
        "conversation_id": str(uuid.uuid4()),
        "is_loading": False,
        "loading_index": 0,
        "loading_messages": [
            "Analyzing policy documents...",
            "Retrieving contextual evidence...",
            "Grounding response...",
            "Synthesizing insights...",
        ],
        "service_mode": "mock",
        "model_status": "Mock Assistant",
        "has_greeted": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def start_new_chat() -> None:
    if st.session_state.messages:
        latest_user_message = next(
            (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"),
            "Untitled conversation",
        )
        
        # Check if this ID already exists in history to avoid duplicates
        existing_idx = next((i for i, item in enumerate(st.session_state.history) 
                             if item["id"] == st.session_state.conversation_id), -1)
        
        entry = {
            "title": latest_user_message[:55],
            "messages": st.session_state.messages.copy(),
            "id": st.session_state.conversation_id
        }
        
        if existing_idx != -1:
            # Update existing entry and move to top
            st.session_state.history.pop(existing_idx)
            st.session_state.history.insert(0, entry)
        else:
            # Insert new entry
            st.session_state.history.insert(0, entry)
            
        st.session_state.history = st.session_state.history[:8]

    st.session_state.messages = []
    st.session_state.conversation_id = str(uuid.uuid4())
    st.session_state.is_loading = False
    st.session_state.has_greeted = False



def switch_chat(chat_id: str) -> None:
    """Switch the current view to a specific chat from history."""
    for item in st.session_state.history:
        if item["id"] == chat_id:
            # Swap current chat into history and load selected chat
            current_title = next(
                (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"),
                "Untitled conversation",
            )
            
            # Simple swap logic: find index and replace
            selected_messages = item["messages"]
            selected_id = item["id"]
            
            # Note: In a real app we'd manage this more robustly, 
            # but for this session state we'll just update the current view.
            st.session_state.messages = selected_messages
            st.session_state.conversation_id = selected_id
            st.session_state.has_greeted = True
            break

