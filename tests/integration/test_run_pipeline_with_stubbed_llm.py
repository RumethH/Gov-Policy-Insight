import pytest
from langchain_core.documents import Document

from src.chains import RAGChain


@pytest.mark.integration
def test_run_pipeline_with_stubbed_components(monkeypatch) -> None:
    chain = object.__new__(RAGChain)
    chain.security = type(
        "S",
        (),
        {"check_injection": lambda self, text: False, "redact_pii": lambda self, text: text},
    )()
    chain.rewrite_query = lambda q: [q]  # noqa: ARG005
    chain.retrieve_docs = lambda q, k=5: [  # noqa: ARG005
        Document(
            page_content="Policy says agencies must report cyber incidents in 24 hours.",
            metadata={"source": "nsw_cyber_policy.pdf", "page": 2},
        )
    ]
    chain.rerank_docs = lambda query, docs: docs  # noqa: ARG005
    chain.generate_response = lambda query, docs: {  # noqa: ARG005
        "answer": "Report incidents in 24 hours [nsw_cyber_policy.pdf, Page 2].",
        "citations": [{"source": "nsw_cyber_policy.pdf", "page": 2}],
    }

    monkeypatch.setenv("PII_REDACTION_ENABLED", "false")
    result = chain.run("What is incident reporting SLA?")
    assert "24 hours" in result["answer"]
    assert result["citations"] == [{"source": "nsw_cyber_policy.pdf", "page": 2}]
