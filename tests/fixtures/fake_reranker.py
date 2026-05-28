from __future__ import annotations

from typing import Any


class LengthReranker:
    """Ranks longer passages first to keep behavior deterministic."""

    def rerank(self, rerank_request: Any) -> list[dict[str, Any]]:
        return sorted(rerank_request.passages, key=lambda p: len(p["text"]), reverse=True)
