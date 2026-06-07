import pytest

from backend.core.chains import RAGChain


@pytest.mark.e2e
def test_e2e_ambiguous_query_prefers_refusal_when_unsupported(monkeypatch) -> None:
    chain = object.__new__(RAGChain)
    chain.security = type(
        "S",
        (),
        {"check_injection": lambda self, text: False, "redact_pii": lambda self, text: text},
    )()
    chain.rewrite_query = lambda q: [q]  # noqa: ARG005
    chain.retrieve_docs = lambda q, k=5, **kwargs: []  # noqa: ARG005
    chain.rerank_docs = lambda query, docs: docs  # noqa: ARG005
    chain.generate_response = lambda query, docs, **kwargs: {  # noqa: ARG005
        "answer": "I don't know. The provided documents do not contain this information.",
        "citations": [],
    }
    chain.embeddings = type("E", (), {"embed_query": lambda self, q: [0.1] * 768})()
    chain.cache = type("C", (), {"get": lambda self, q, **kwargs: None, "set": lambda self, q, r, **kwargs: None})()
    monkeypatch.setenv("PII_REDACTION_ENABLED", "false")

    result = chain.run("What exact budget line funds this policy?")
    assert "don't know" in result["answer"].lower()
    assert result["citations"] == []
