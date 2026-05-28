from __future__ import annotations

from typing import List


class DeterministicEmbeddings:
    """Simple deterministic embedding function for local integration tests."""

    def _vec(self, text: str) -> List[float]:
        base = sum(ord(ch) for ch in text)
        return [
            float((base % 97) / 97.0),
            float((len(text) % 31) / 31.0),
            float(((base + len(text)) % 53) / 53.0),
            float((text.count("policy") % 7) / 7.0),
            float((text.count("NSW") % 5) / 5.0),
        ]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._vec(text)
