from __future__ import annotations

import re
from typing import Iterable

from langchain_core.documents import Document


def has_citation(answer: str) -> bool:
    pattern = re.compile(r"\[[^,\]]+,\s*Page\s+\d+\]")
    return bool(pattern.search(answer))


def unsupported_claim_detected(answer: str, context_docs: Iterable[Document]) -> bool:
    context_text = " ".join(d.page_content.lower() for d in context_docs)
    answer_tokens = [t for t in re.findall(r"[a-zA-Z]{5,}", answer.lower())]
    if not answer_tokens:
        return False
    overlap = sum(1 for tok in answer_tokens if tok in context_text)
    return overlap / len(answer_tokens) < 0.35
