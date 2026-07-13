"""Tests for quality gate Clerk token bootstrap."""

import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "evals"))
import quality_gate  # noqa: E402


def test_bootstrap_clerk_token_mints_when_secret_present(monkeypatch):
    monkeypatch.delenv("CAMPUSQ_CLERK_TOKEN", raising=False)
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_example")
    with patch("mint_clerk_token.mint_clerk_session_token", return_value="fresh-jwt"):
        quality_gate.bootstrap_clerk_token()
    assert os.environ["CAMPUSQ_CLERK_TOKEN"] == "fresh-jwt"


def test_bootstrap_clerk_token_skips_when_token_already_set(monkeypatch):
    monkeypatch.setenv("CAMPUSQ_CLERK_TOKEN", "existing-jwt")
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_example")
    with patch("mint_clerk_token.mint_clerk_session_token") as mint:
        quality_gate.bootstrap_clerk_token()
        mint.assert_not_called()
