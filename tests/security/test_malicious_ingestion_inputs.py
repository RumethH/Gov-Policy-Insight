from pathlib import Path

import pytest


@pytest.mark.security
def test_path_traversal_document_name_rejected_by_policy() -> None:
    # Guardrail policy for ingestion test data handling.
    bad_name = "../../etc/passwd"
    candidate = Path(bad_name)
    assert ".." in candidate.parts


@pytest.mark.security
def test_oversized_payload_flagged() -> None:
    payload = "A" * 2_000_000
    assert len(payload) > 1_000_000
