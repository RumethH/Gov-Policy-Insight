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

    # 1. Add to state and render immediately
    state.messages.append({"role": "user", "content": prompt, "citations": []})
    with st.chat_message("user"):
        st.markdown(prompt)

    state.is_loading = True
    
    # 2. Handle Assistant Response
    if state.service_mode == "local_rag":
        with st.spinner("Thinking..."):
            try:
                response_stream = service.ask(prompt=prompt, conversation_id=state.conversation_id, stream=True)
            except Exception as e:
                st.error(f"Error connecting to RAG service: {e}")
                state.is_loading = False
                return
            
        with st.chat_message("assistant"):
            # Use lists to capture data from the generator closure
            full_text_container = [""]
            citations_container = [[]]
            
            def get_stream_text():
                try:
                    for chunk in response_stream:
                        text = chunk.get("answer_chunk", "")
                        full_text_container[0] += text
                        citations_container[0] = chunk.get("citations", [])
                        yield text
                except Exception as e:
                    yield f"\n\n⚠️ *Stream interrupted: {e}*"

            st.write_stream(get_stream_text())
            
            # Use captured values
            final_text = full_text_container[0]
            final_citations = citations_container[0]
            
            if not final_text:
                final_text = "I'm sorry, I couldn't generate a response. Please try rephrasing your question."
                st.warning(final_text)
            
            from components.chat_thread import _render_citations
            _render_citations(final_citations)
            
            state.messages.append(
                {
                    "role": "assistant",
                    "content": final_text,
                    "citations": final_citations,
                }
            )
    else:
        with st.spinner("Thinking..."):
            try:
                response = service.ask(prompt=prompt, conversation_id=state.conversation_id, stream=False)
                final_text = response.get("answer", "")
                final_citations = response.get("citations", [])
            except Exception as e:
                final_text = f"Error: {e}"
                final_citations = []
        
        if not final_text:
            final_text = "No response received from the service."

        with st.chat_message("assistant"):
            st.markdown(final_text)
            from components.chat_thread import _render_citations
            _render_citations(final_citations)
            
        state.messages.append(
            {
                "role": "assistant",
                "content": final_text,
                "citations": final_citations,
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
