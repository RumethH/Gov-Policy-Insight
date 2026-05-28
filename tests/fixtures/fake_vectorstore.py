from __future__ import annotations

from langchain_core.documents import Document


class InMemoryVectorStore:
    def __init__(self, mapping: dict[str, list[Document]]):
        self.mapping = mapping

    def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        return self.mapping.get(query, [])[:k]
