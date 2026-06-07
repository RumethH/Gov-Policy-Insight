from types import SimpleNamespace

import pytest

from backend.core.security import SecurityManager


class StubAnalyzer:
    def analyze(self, text: str, entities: list[str], language: str) -> list[dict]:
        assert language == "en"
        assert "PERSON" in entities
        return [{"start": 11, "end": 19, "entity_type": "PERSON"}]


class StubAnonymizer:
    def anonymize(self, text: str, analyzer_results: list[dict], operators: dict) -> SimpleNamespace:
        _ = (analyzer_results, operators)
        return SimpleNamespace(text=text.replace("John Doe", "[NAME]"))


@pytest.mark.unit
def test_redact_pii_replaces_expected_tokens() -> None:
    security = object.__new__(SecurityManager)
    security.analyzer = StubAnalyzer()
    security.anonymizer = StubAnonymizer()

    redacted = security.redact_pii("Citizen John Doe submitted a request.")
    assert "[NAME]" in redacted
    assert "John Doe" not in redacted
