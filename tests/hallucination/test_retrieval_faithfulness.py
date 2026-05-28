import pytest
from langchain_core.documents import Document

from tests.hallucination.evaluators import unsupported_claim_detected


@pytest.mark.hallucination
def test_response_aligned_with_source_chunks() -> None:
    context = [
        Document(
            page_content="Risk management plans must be reviewed annually.",
            metadata={"source": "risk.pdf", "page": 6},
        ),
        Document(
            page_content="Review outcomes must be recorded in a governance register.",
            metadata={"source": "risk.pdf", "page": 7},
        ),
    ]
    answer = "Risk plans are reviewed annually and outcomes are recorded in governance registers."
    assert unsupported_claim_detected(answer, context) is False
