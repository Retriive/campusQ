"""Tests for quality gate Clerk auth helpers."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# evals/ is not a package; import via path like other backend tests.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "evals"))
import quality_gate  # noqa: E402


def test_chat_auth_headers_with_token(monkeypatch):
    monkeypatch.setenv("CAMPUSQ_CLERK_TOKEN", "test-jwt")
    assert quality_gate.chat_auth_headers() == {"Authorization": "Bearer test-jwt"}


def test_chat_auth_headers_without_token(monkeypatch):
    monkeypatch.delenv("CAMPUSQ_CLERK_TOKEN", raising=False)
    assert quality_gate.chat_auth_headers() == {}


def test_ensure_chat_auth_skips_localhost(monkeypatch):
    monkeypatch.delenv("CAMPUSQ_CLERK_TOKEN", raising=False)
    with patch("quality_gate.requests.post") as post:
        quality_gate.ensure_chat_auth("http://localhost:8000")
        post.assert_not_called()


def test_ensure_chat_auth_exits_on_401(monkeypatch):
    monkeypatch.delenv("CAMPUSQ_CLERK_TOKEN", raising=False)
    resp = MagicMock()
    resp.status_code = 401
    with patch("quality_gate.requests.post", return_value=resp):
        with pytest.raises(SystemExit) as exc:
            quality_gate.ensure_chat_auth("https://api.example.com")
        assert exc.value.code == 2
    resp.close.assert_called_once()
