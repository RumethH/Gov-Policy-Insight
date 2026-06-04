import time
import streamlit as st

from components.chat_thread import render_chat_thread
from components.composer import render_composer
from components.header import render_header
from components.loading import render_loading_state
from components.sidebar import render_sidebar
from services.chat_service import build_chat_service
from utils.state import init_session_state, start_new_chat


st.set_page_config(
    page_title="chatGPI",
    page_icon=":speech_balloon:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def handle_user_prompt(prompt: str) -> None:
    """Process a user prompt through the configured chat service."""
    state = st.session_state
    service = build_chat_service(state.service_mode)

    state.messages.append({"role": "user", "content": prompt, "citations": []})
    state.is_loading = True
    
    # Simple simulated loading with standard spinner
    with st.spinner("Thinking..."):
        response = service.ask(prompt=prompt, conversation_id=state.conversation_id, stream=False)

    state.messages.append(
        {
            "role": "assistant",
            "content": response["answer"],
            "citations": response.get("citations", []),
        }
    )
    state.is_loading = False


def maybe_add_greeting() -> None:
    state = st.session_state
    if state.messages or state.has_greeted:
        return

    service = build_chat_service(state.service_mode)
    greeting = service.greeting(state.conversation_id)
    state.messages.append({"role": "assistant", "content": greeting, "citations": []})
    state.has_greeted = True


def main() -> None:
    init_session_state()

    with st.sidebar:
        sidebar_action = render_sidebar()
        if sidebar_action == "new_chat":
            start_new_chat()
            st.rerun()

    maybe_add_greeting()
    render_header()
    render_chat_thread(st.session_state.messages)

    prompt = render_composer(disabled=st.session_state.is_loading)
    if prompt:
        handle_user_prompt(prompt)
        st.rerun()


if __name__ == "__main__":
    main()
