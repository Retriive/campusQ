"""Tests for optional_user (guest-friendly chat auth)."""

import asyncio
from unittest.mock import MagicMock, patch

import auth


def test_optional_user_allows_anonymous_when_require_auth_on(monkeypatch):
    auth._REQUIRE_AUTH = True
    auth._CLERK_JWKS_URL = "https://example.com/.well-known/jwks.json"
    auth._QUALITY_GATE_KEY = ""
    request = MagicMock()
    request.headers = {}
    assert asyncio.run(auth.optional_user(request)) == "anonymous"


def test_optional_user_honors_valid_token(monkeypatch):
    auth._REQUIRE_AUTH = True
    auth._CLERK_JWKS_URL = "https://example.com/.well-known/jwks.json"
    auth._QUALITY_GATE_KEY = ""
    request = MagicMock()
    request.headers = {"authorization": "Bearer good-token"}
    with patch.object(auth, "_verify_token", return_value={"sub": "user_abc"}):
        assert asyncio.run(auth.optional_user(request)) == "user_abc"


def test_optional_user_invalid_token_falls_back_to_anonymous(monkeypatch):
    auth._REQUIRE_AUTH = True
    auth._CLERK_JWKS_URL = "https://example.com/.well-known/jwks.json"
    auth._QUALITY_GATE_KEY = ""
    request = MagicMock()
    request.headers = {"authorization": "Bearer bad-token"}
    with patch.object(auth, "_verify_token", side_effect=Exception("bad")):
        assert asyncio.run(auth.optional_user(request)) == "anonymous"
