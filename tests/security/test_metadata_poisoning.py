import pytest
from langchain_core.documents import Document

from backend.core.chains import RAGChain


@pytest.mark.security
def test_generate_response_handles_poison_like_metadata_strings(mocker) -> None:
    class FakeResponse:
        content = "Answer with citation [Unknown, Page Unknown]."

    class FakePipeline:
        def invoke(self, payload: dict) -> FakeResponse:
            assert "Context" not in payload
            return FakeResponse()

    class FakePrompt:
        def __or__(self, llm):  # noqa: ANN001
            _ = llm
            return FakePipeline()

    chain = object.__new__(RAGChain)
    chain.llm = object()
    mocker.patch("backend.core.chains.ChatPromptTemplate.from_template", return_value=FakePrompt())
    docs = [Document(page_content="chunk text", metadata={"source": "../../../tmp/evil<script>.pdf"})]

    result = chain.generate_response("query", docs)
    assert "answer" in result
    assert result["citations"][0]["source"] == "evil<script>.pdf"
