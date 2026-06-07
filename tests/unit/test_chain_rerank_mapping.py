import pytest
from langchain_core.documents import Document

from backend.core.chains import RAGChain
from tests.fixtures.fake_reranker import LengthReranker


@pytest.mark.unit
def test_rerank_docs_preserves_metadata_and_orders_by_rank() -> None:
    chain = object.__new__(RAGChain)
    chain.ranker = LengthReranker()
    docs = [
        Document(page_content="short text", metadata={"source": "a.pdf", "page": 1}),
        Document(page_content="much longer policy excerpt text", metadata={"source": "b.pdf", "page": 2}),
    ]

    ranked = chain.rerank_docs("query", docs)

    assert ranked[0].metadata["source"] == "b.pdf"
    assert ranked[1].metadata["source"] == "a.pdf"


@pytest.mark.unit
def test_rerank_docs_empty_input_returns_empty() -> None:
    chain = object.__new__(RAGChain)
    chain.ranker = LengthReranker()
    assert chain.rerank_docs("query", []) == []
