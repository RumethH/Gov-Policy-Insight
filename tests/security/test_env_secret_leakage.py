import os

import pytest


@pytest.mark.security
def test_no_real_google_api_key_required_for_test_suite(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert os.getenv("GOOGLE_API_KEY") is None
