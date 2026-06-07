from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import pytest
from langchain_core.documents import Document

from backend.core.chains import RAGChain


@dataclass
class FakeResponse:
    content: str


class FakeLLM:
    def __init__(self, rewrite_text: str, answer_text: str):
        self.rewrite_text = rewrite_text
        self.answer_text = answer_text

    def invoke(self, payload: dict[str, Any]) -> FakeResponse:
        if "question" in payload:
            return FakeResponse(content=self.rewrite_text)
        return FakeResponse(content=self.answer_text)


class FakeRanker:
    def rerank(self, rerank_request: Any) -> list[dict[str, Any]]:
        passages = rerank_request.passages
        return sorted(passages, key=lambda p: len(p["text"]), reverse=True)


class FakeVectorStore:
    def __init__(self, docs_by_query: dict[str, list[Document]]):
        self.docs_by_query = docs_by_query

    def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        return self.docs_by_query.get(query, [])[:k]


class FakeSecurity:
    def __init__(self, inject: bool = False):
        self.inject = inject

    def check_injection(self, text: str) -> bool:
        return self.inject

    def redact_pii(self, text: str) -> str:
        return text.replace("John Doe", "[NAME]")


@pytest.fixture
def policy_documents() -> list[Document]:
    return [
        Document(
            page_content="NSW agencies must report cyber incidents within 24 hours.",
            metadata={"source": "nsw_cyber_policy.pdf", "page": 2},
        ),
        Document(
            page_content="Risk management plans must be reviewed annually.",
            metadata={"source": "risk_management.pdf", "page": 6},
        ),
        Document(
            page_content="Climate adaptation programs require yearly progress reporting.",
            metadata={"source": "climate_policy.pdf", "page": 4},
        ),
    ]


@pytest.fixture
def fake_chain(policy_documents: list[Document]) -> RAGChain:
    chain = object.__new__(RAGChain)
    chain.llm = FakeLLM(
        rewrite_text="\n".join(
            [
                "What are cyber obligations for NSW agencies?",
                "NSW cyber incident reporting obligations",
                "Cyber policy reporting timeline NSW",
                "Policy requirements for cyber incidents",
                "Government cyber incident policy NSW",
            ]
        ),
        answer_text="Cyber incidents must be reported in 24 hours [nsw_cyber_policy.pdf, Page 2].",
    )
    chain.vectorstore = FakeVectorStore(
        docs_by_query={
            "What is the NSW Cyber Security Policy?": policy_documents,
            "NSW cyber incident reporting obligations": policy_documents[:2],
        }
    )
    chain.embeddings = type("E", (), {"embed_query": lambda self, q: [0.1] * 768})()
    chain.cache = type("C", (), {
        "get": lambda self, q, **kwargs: None, 
        "set": lambda self, q, r, **kwargs: None
    })()
    chain.ranker = FakeRanker()
    chain.security = FakeSecurity(inject=False)
    
    # Override retrieve_docs to handle kwargs
    original_search = chain.vectorstore.similarity_search
    chain.retrieve_docs = lambda query, k=10, **kwargs: original_search(query, k=k)
    
    return chain


@pytest.fixture
def docs_factory() -> callable:
    def _build(texts: Iterable[str], source: str = "test_source.pdf", page_start: int = 1) -> list[Document]:
        return [
            Document(page_content=text, metadata={"source": source, "page": page_start + idx})
            for idx, text in enumerate(texts)
        ]

    return _build
