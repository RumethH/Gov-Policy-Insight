import pytest
from langchain_core.documents import Document

from backend.core.chains import RAGChain


@pytest.mark.e2e
def test_e2e_policy_query_returns_grounded_answer(monkeypatch) -> None:
    chain = object.__new__(RAGChain)
    chain.security = type(
        "S",
        (),
        {"check_injection": lambda self, text: False, "redact_pii": lambda self, text: text},
    )()
    chain.rewrite_query = lambda q: [q]  # noqa: ARG005
    chain.retrieve_docs = lambda q, k=5, **kwargs: [  # noqa: ARG005
        Document(
            page_content="NSW agencies must report cyber incidents within 24 hours.",
            metadata={"source": "nsw_cyber_policy.pdf", "page": 2},
        )
    ]
    chain.rerank_docs = lambda query, docs: docs  # noqa: ARG005
    chain.generate_response = lambda query, docs, **kwargs: {  # noqa: ARG005
        "answer": "NSW agencies must report incidents within 24 hours [nsw_cyber_policy.pdf, Page 2].",
        "citations": [{"source": "nsw_cyber_policy.pdf", "page": 2}],
    }
    chain.embeddings = type("E", (), {"embed_query": lambda self, q: [0.1] * 768})()
    chain.cache = type("C", (), {"get": lambda self, q, **kwargs: None, "set": lambda self, q, r, **kwargs: None})()
    monkeypatch.setenv("PII_REDACTION_ENABLED", "false")

    result = chain.run("What is the NSW cyber incident reporting requirement?")
    assert "[nsw_cyber_policy.pdf, Page 2]" in result["answer"]
    assert len(result["citations"]) == 1
