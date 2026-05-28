from dataclasses import dataclass

import pytest

from src.chains import RAGChain


@dataclass
class FakeResponse:
    content: str


class FakePipeline:
    def invoke(self, payload: dict) -> FakeResponse:
        _ = payload
        return FakeResponse(
            content="Variant A\nVariant B\nVariant C\nVariant D\nVariant E\n"
        )


class FakePrompt:
    def __or__(self, llm):  # noqa: ANN001
        _ = llm
        return FakePipeline()


@pytest.mark.unit
def test_rewrite_query_parses_lines_and_includes_original(mocker) -> None:
    chain = object.__new__(RAGChain)
    chain.llm = object()
    mocker.patch("src.chains.ChatPromptTemplate.from_template", return_value=FakePrompt())

    original = "Original policy query"
    queries = chain.rewrite_query(original)

    assert queries[:5] == ["Variant A", "Variant B", "Variant C", "Variant D", "Variant E"]
    assert original in queries
