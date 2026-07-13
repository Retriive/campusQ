"""Tests for require_signed_in (account-only routes)."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

os_env = __import__("os").environ
os_env.setdefault("CLERK_JWKS_URL", "https://example.com/.well-known/jwks.json")

import auth  # noqa: E402


def test_require_signed_in_missing_token():
    auth._CLERK_JWKS_URL = "https://example.com/.well-known/jwks.json"
    auth._QUALITY_GATE_KEY = ""
    request = MagicMock()
    request.headers = {}
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_signed_in(request))
    assert exc.value.status_code == 401


def test_require_signed_in_rejects_quality_gate_key(monkeypatch):
    auth._CLERK_JWKS_URL = "https://example.com/.well-known/jwks.json"
    auth._QUALITY_GATE_KEY = "gate-secret"
    request = MagicMock()
    request.headers = {"x-quality-gate-key": "gate-secret"}
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_signed_in(request))
    assert exc.value.status_code == 403


def test_require_signed_in_valid_token():
    auth._CLERK_JWKS_URL = "https://example.com/.well-known/jwks.json"
    auth._QUALITY_GATE_KEY = ""
    request = MagicMock()
    request.headers = {"authorization": "Bearer good-token"}
    with patch.object(auth, "_verify_token", return_value={"sub": "user_123"}):
        assert asyncio.run(auth.require_signed_in(request)) == "user_123"


def test_require_signed_in_unconfigured_jwks():
    auth._CLERK_JWKS_URL = ""
    auth._QUALITY_GATE_KEY = ""
    request = MagicMock()
    request.headers = {"authorization": "Bearer good-token"}
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_signed_in(request))
    assert exc.value.status_code == 503
