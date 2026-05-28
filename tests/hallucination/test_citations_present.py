import pytest

from tests.hallucination.evaluators import has_citation


@pytest.mark.hallucination
@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("Agencies must report incidents [policy.pdf, Page 2].", True),
        ("Agencies must report incidents quickly.", False),
    ],
)
def test_has_citation(answer: str, expected: bool) -> None:
    assert has_citation(answer) is expected
