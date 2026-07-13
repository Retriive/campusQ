"""Tests for Clerk token minting used by the quality gate."""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "evals"))
import mint_clerk_token  # noqa: E402


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_mint_clerk_session_token_creates_user_and_session():
    secret = "sk_test_example"
    with patch("mint_clerk_token.requests.get", return_value=_Resp([])):
        with patch("mint_clerk_token.requests.post") as post:
            post.side_effect = [
                _Resp({"id": "user_123"}),
                _Resp({"id": "sess_456"}),
                _Resp({"jwt": "jwt-token"}),
            ]
            with patch.dict(os.environ, {"CLERK_SECRET_KEY": secret}, clear=False):
                assert mint_clerk_token.mint_clerk_session_token() == "jwt-token"
            assert post.call_count == 3


def test_mint_clerk_session_token_reuses_existing_user():
    secret = "sk_test_example"
    with patch(
        "mint_clerk_token.requests.get",
        return_value=_Resp([{
            "id": "user_existing",
            "email_addresses": [{"email_address": "quality-gate@retriive.com"}],
        }]),
    ):
        with patch("mint_clerk_token.requests.post") as post:
            post.side_effect = [
                _Resp({"id": "sess_456"}),
                _Resp({"jwt": "jwt-token"}),
            ]
            with patch.dict(os.environ, {"CLERK_SECRET_KEY": secret}, clear=False):
                assert mint_clerk_token.mint_clerk_session_token() == "jwt-token"
            assert post.call_count == 2


def test_mint_clerk_session_token_missing_secret():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match="CLERK_SECRET_KEY"):
            mint_clerk_token.mint_clerk_session_token()
