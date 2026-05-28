import pytest
from langchain_core.documents import Document

from src.chains import RAGChain
from tests.fixtures.fake_reranker import LengthReranker
from tests.fixtures.fake_vectorstore import InMemoryVectorStore


@pytest.mark.integration
def test_retrieval_rerank_and_context_selection_pipeline() -> None:
    docs = [
        Document(page_content="short", metadata={"source": "s.pdf", "page": 1}),
        Document(
            page_content="longer policy passage describing cyber obligations in detail",
            metadata={"source": "l.pdf", "page": 2},
        ),
    ]
    chain = object.__new__(RAGChain)
    chain.vectorstore = InMemoryVectorStore({"q": docs})
    chain.ranker = LengthReranker()

    retrieved = chain.retrieve_docs("q", k=5)
    reranked = chain.rerank_docs("q", retrieved)

    assert len(retrieved) == 2
    assert reranked[0].metadata["source"] == "l.pdf"
