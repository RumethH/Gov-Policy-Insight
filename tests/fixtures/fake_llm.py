from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FakeLLMResponse:
    content: str


class DeterministicLLM:
    def __init__(self, rewrite_lines: list[str], answer_text: str):
        self.rewrite_lines = rewrite_lines
        self.answer_text = answer_text

    def invoke(self, payload: dict[str, Any]) -> FakeLLMResponse:
        if "question" in payload:
            return FakeLLMResponse(content="\n".join(self.rewrite_lines))
        return FakeLLMResponse(content=self.answer_text)
