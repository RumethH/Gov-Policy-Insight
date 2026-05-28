import pytest
from langchain_core.documents import Document

from src.chains import RAGChain


@pytest.mark.e2e
def test_e2e_conflicting_docs_response_retains_citations(monkeypatch) -> None:
    chain = object.__new__(RAGChain)
    chain.security = type(
        "S",
        (),
        {"check_injection": lambda self, text: False, "redact_pii": lambda self, text: text},
    )()
    chain.rewrite_query = lambda q: [q]  # noqa: ARG005
    chain.retrieve_docs = lambda q, k=5: [  # noqa: ARG005
        Document(page_content="Policy A says annual review.", metadata={"source": "a.pdf", "page": 3}),
        Document(page_content="Policy B says quarterly review.", metadata={"source": "b.pdf", "page": 7}),
    ]
    chain.rerank_docs = lambda query, docs: docs  # noqa: ARG005
    chain.generate_response = lambda query, docs: {  # noqa: ARG005
        "answer": (
            "Documents conflict: annual and quarterly cycles are both specified "
            "[a.pdf, Page 3] [b.pdf, Page 7]."
        ),
        "citations": [{"source": "a.pdf", "page": 3}, {"source": "b.pdf", "page": 7}],
    }
    monkeypatch.setenv("PII_REDACTION_ENABLED", "false")

    result = chain.run("How often should policy reviews occur?")
    assert "conflict" in result["answer"].lower()
    assert len(result["citations"]) == 2
