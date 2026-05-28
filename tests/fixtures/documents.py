from __future__ import annotations

from langchain_core.documents import Document


def make_policy_doc(content: str, source: str, page: int) -> Document:
    return Document(page_content=content, metadata={"source": source, "page": page})
