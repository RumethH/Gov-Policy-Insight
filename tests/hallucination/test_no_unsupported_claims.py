import pytest
from langchain_core.documents import Document

from tests.hallucination.evaluators import unsupported_claim_detected


@pytest.mark.hallucination
def test_detects_unsupported_claims() -> None:
    docs = [
        Document(
            page_content="NSW agencies must report cyber incidents within 24 hours.",
            metadata={"source": "policy.pdf", "page": 2},
        )
    ]
    unsupported = "The policy allocates a $500 million annual budget to this requirement."
    assert unsupported_claim_detected(unsupported, docs) is True


@pytest.mark.hallucination
def test_allows_supported_claims() -> None:
    docs = [
        Document(
            page_content="NSW agencies must report cyber incidents within 24 hours.",
            metadata={"source": "policy.pdf", "page": 2},
        )
    ]
    supported = "Agencies must report cyber incidents within 24 hours."
    assert unsupported_claim_detected(supported, docs) is False
