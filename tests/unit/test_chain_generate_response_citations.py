from dataclasses import dataclass

import pytest
from langchain_core.documents import Document

from src.chains import RAGChain


@dataclass
class FakeResponse:
    content: str


class FakePipeline:
    def invoke(self, payload: dict) -> FakeResponse:
        assert "context" in payload
        assert "query" in payload
        return FakeResponse(content="Grounded answer [policy.pdf, Page 2].")


class FakePrompt:
    def __or__(self, llm):  # noqa: ANN001
        _ = llm
        return FakePipeline()


@pytest.mark.unit
def test_generate_response_builds_unique_citations(mocker) -> None:
    chain = object.__new__(RAGChain)
    chain.llm = object()
    mocker.patch("src.chains.ChatPromptTemplate.from_template", return_value=FakePrompt())
    docs = [
        Document(page_content="A", metadata={"source": "/tmp/policy.pdf", "page": 2}),
        Document(page_content="B", metadata={"source": "/tmp/policy.pdf", "page": 2}),
        Document(page_content="C", metadata={"source": "/tmp/policy2.pdf", "page": 4}),
    ]

    result = chain.generate_response("question", docs)

    assert "answer" in result
    assert len(result["citations"]) == 2
    assert result["citations"][0] == {"source": "policy.pdf", "page": 2}
