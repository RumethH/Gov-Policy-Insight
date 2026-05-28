import pytest
from langchain_core.documents import Document

from src.chains import RAGChain


@pytest.mark.e2e
def test_e2e_policy_query_returns_grounded_answer(monkeypatch) -> None:
    chain = object.__new__(RAGChain)
    chain.security = type(
        "S",
        (),
        {"check_injection": lambda self, text: False, "redact_pii": lambda self, text: text},
    )()
    chain.rewrite_query = lambda q: [q]  # noqa: ARG005
    chain.retrieve_docs = lambda q, k=5: [  # noqa: ARG005
        Document(
            page_content="NSW agencies must report cyber incidents within 24 hours.",
            metadata={"source": "nsw_cyber_policy.pdf", "page": 2},
        )
    ]
    chain.rerank_docs = lambda query, docs: docs  # noqa: ARG005
    chain.generate_response = lambda query, docs: {  # noqa: ARG005
        "answer": "NSW agencies must report incidents within 24 hours [nsw_cyber_policy.pdf, Page 2].",
        "citations": [{"source": "nsw_cyber_policy.pdf", "page": 2}],
    }
    monkeypatch.setenv("PII_REDACTION_ENABLED", "false")

    result = chain.run("What is the NSW cyber incident reporting requirement?")
    assert "[nsw_cyber_policy.pdf, Page 2]" in result["answer"]
    assert len(result["citations"]) == 1
