import pytest

from src.chains import RAGChain


@pytest.mark.e2e
def test_e2e_ambiguous_query_prefers_refusal_when_unsupported(monkeypatch) -> None:
    chain = object.__new__(RAGChain)
    chain.security = type(
        "S",
        (),
        {"check_injection": lambda self, text: False, "redact_pii": lambda self, text: text},
    )()
    chain.rewrite_query = lambda q: [q]  # noqa: ARG005
    chain.retrieve_docs = lambda q, k=5: []  # noqa: ARG005
    chain.rerank_docs = lambda query, docs: docs  # noqa: ARG005
    chain.generate_response = lambda query, docs: {  # noqa: ARG005
        "answer": "I don't know. The provided documents do not contain this information.",
        "citations": [],
    }
    monkeypatch.setenv("PII_REDACTION_ENABLED", "false")

    result = chain.run("What exact budget line funds this policy?")
    assert "don't know" in result["answer"].lower()
    assert result["citations"] == []
