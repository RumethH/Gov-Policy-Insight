from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional, Protocol

import requests


class ChatService(Protocol):
    def ask(self, prompt: str, conversation_id: str, stream: bool = False, api_key: Optional[str] = None) -> Dict[str, Any]:
        ...

    def greeting(self, conversation_id: str) -> str:
        ...


class MockChatService:
    """Local development fallback with realistic shape."""

    def ask(self, prompt: str, conversation_id: str, stream: bool = False, api_key: Optional[str] = None) -> Any:
        _ = conversation_id
        answer = (
            "Based on current policy guidance, agencies should establish clear ownership, "
            "document controls, and periodic compliance reviews. If you share a specific "
            "policy title, I can provide a grounded summary with obligations and timelines."
        )
        citations = [{"source": "Policy-Guide-Sample.pdf", "page": 3}]
        
        if stream:
            def chunk_generator():
                time.sleep(1.2)
                words = answer.split(" ")
                for i, word in enumerate(words):
                    yield {
                        "answer_chunk": word + (" " if i < len(words) - 1 else ""),
                        "citations": citations
                    }
            return chunk_generator()
        
        return {
            "answer": answer,
            "citations": citations,
            "metadata": {"mode": "mock"},
        }

    def greeting(self, conversation_id: str) -> str:
        _ = conversation_id
        return (
            "Hello, I am **chatGPI**. I can help you interpret government policies, "
            "extract obligations, and ground answers with citations. "
            "What policy question would you like to start with?"
        )


import sys
from pathlib import Path

class LocalRAGChatService:
    """Adapter around the existing in-repo RAG chain."""

    def __init__(self) -> None:
        # Ensure project root is in sys.path
        root = Path(__file__).parents[2]
        if str(root) not in sys.path:
            sys.path.append(str(root))
            
        try:
            from backend.core.chains import RAGChain  # lazy import to keep startup fast
        except ImportError as exc:
            raise RuntimeError(f"Unable to import local RAG chain: {exc}") from exc
        self._chain = RAGChain()

    def ask(self, prompt: str, conversation_id: str, stream: bool = False, api_key: Optional[str] = None) -> Any:
        _ = conversation_id
        if stream:
            stream_gen, citations = self._chain.run(prompt, stream=True, api_key=api_key)
            def chunk_generator():
                for chunk in stream_gen:
                    yield {"answer_chunk": chunk.content, "citations": citations}
            return chunk_generator()
        else:
            return self._chain.run(prompt, stream=False, api_key=api_key)

    def greeting(self, conversation_id: str) -> str:
        _ = conversation_id
        try:
            # Use the model directly for a natural first-touch greeting.
            response = self._chain.llm.invoke(
                "Write one concise welcome message for chatGPI, a Government Policy "
                "Intelligence assistant specializing in NSW Government policies. "
                "Tone: calm, professional, and helpful. "
                "Max 35 words. Invite the user to ask a NSW policy question."
            )
            text = (response.content or "").strip()
            return text or MockChatService().greeting(conversation_id)
        except Exception:
            return MockChatService().greeting(conversation_id)


class FastAPIChatService:
    """REST-ready service contract for future deployment."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def ask(self, prompt: str, conversation_id: str, stream: bool = False, api_key: Optional[str] = None) -> Dict[str, Any]:
        payload = {"prompt": prompt, "conversation_id": conversation_id, "stream": stream}
        headers = {"X-Gemini-API-Key": api_key} if api_key else {}
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers=headers,
                timeout=45,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "answer": data.get("answer", ""),
                "citations": data.get("citations", []),
                "metadata": data.get("metadata", {}),
            }
        except requests.RequestException as exc:
            return {
                "answer": (
                    "I could not reach the backend service right now. "
                    "Please try again shortly."
                ),
                "citations": [],
                "metadata": {"error": str(exc)},
            }

    def greeting(self, conversation_id: str) -> str:
        payload = {"conversation_id": conversation_id}
        try:
            response = requests.post(
                f"{self.base_url}/chat/greeting",
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("greeting") or MockChatService().greeting(conversation_id)
        except requests.RequestException:
            return MockChatService().greeting(conversation_id)


def build_chat_service(mode: str) -> ChatService:
    if mode == "local_rag":
        try:
            return LocalRAGChatService()
        except Exception as e:
            import streamlit as st
            st.error(f"Failed to initialize Local RAG: {e}")
            # Still return Mock for now but at least show the error
            return MockChatService()

    if mode == "api":
        base_url = os.getenv("CHATGPI_API_BASE_URL", "http://localhost:8000")
        return FastAPIChatService(base_url=base_url)

    return MockChatService()
