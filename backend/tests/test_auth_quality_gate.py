"""Tests for quality-gate shared secret auth."""

import asyncio
import os
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

os.environ.setdefault("REQUIRE_AUTH", "true")
os.environ.setdefault("CLERK_JWKS_URL", "https://example.com/.well-known/jwks.json")

import auth  # noqa: E402


def test_quality_gate_key_authenticates_without_bearer(monkeypatch):
    monkeypatch.setenv("QUALITY_GATE_KEY", "gate-secret")
    auth._QUALITY_GATE_KEY = "gate-secret"
    request = MagicMock()
    request.headers = {"x-quality-gate-key": "gate-secret"}
    assert asyncio.run(auth.require_user(request)) == "quality-gate"


def test_wrong_quality_gate_key_still_requires_bearer(monkeypatch):
    monkeypatch.setenv("QUALITY_GATE_KEY", "gate-secret")
    auth._QUALITY_GATE_KEY = "gate-secret"
    request = MagicMock()
    request.headers = {"x-quality-gate-key": "wrong"}
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_user(request))
    assert exc.value.status_code == 401
