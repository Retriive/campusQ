"""Clerk JWT hardening (issue #48): authorized-parties and audience checks.

Crafts real RS256 tokens with an in-test RSA key and points auth._verify_token
at the matching public key, so we exercise the actual jwt.decode path.
"""
import importlib

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa


@pytest.fixture(autouse=True)
def _restore_auth_module():
    """These tests reload `auth` with custom env; restore a clean module
    afterwards so later tests importing `auth` see default state."""
    yield
    for k in ("CLERK_AUTHORIZED_PARTIES", "CLERK_AUDIENCE", "CLERK_ISSUER"):
        __import__("os").environ.pop(k, None)
    import auth
    importlib.reload(auth)


@pytest.fixture()
def rsa_keys():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return priv, priv.public_key()


def _load_auth(monkeypatch, public_key, **env):
    """Import a fresh auth module with the given env, wired to `public_key`."""
    for k in ("CLERK_AUTHORIZED_PARTIES", "CLERK_AUDIENCE", "CLERK_ISSUER"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import auth
    auth = importlib.reload(auth)

    class _Key:
        def __init__(self, key):
            self.key = key

    class _Client:
        def get_signing_key_from_jwt(self, token):
            return _Key(public_key)

    monkeypatch.setattr(auth, "_get_jwk_client", lambda: _Client())
    return auth


def _token(priv, claims):
    return jwt.encode(claims, priv, algorithm="RS256")


def test_valid_azp_accepted(monkeypatch, rsa_keys):
    priv, pub = rsa_keys
    auth = _load_auth(monkeypatch, pub, CLERK_AUTHORIZED_PARTIES="https://app.retriive.com")
    token = _token(priv, {"sub": "user_1", "azp": "https://app.retriive.com"})
    assert auth._verify_token(token)["sub"] == "user_1"


def test_untrusted_azp_rejected(monkeypatch, rsa_keys):
    priv, pub = rsa_keys
    auth = _load_auth(monkeypatch, pub, CLERK_AUTHORIZED_PARTIES="https://app.retriive.com")
    token = _token(priv, {"sub": "user_1", "azp": "https://evil.example.com"})
    with pytest.raises(jwt.InvalidTokenError):
        auth._verify_token(token)


def test_missing_azp_rejected_when_allowlist_set(monkeypatch, rsa_keys):
    priv, pub = rsa_keys
    auth = _load_auth(monkeypatch, pub, CLERK_AUTHORIZED_PARTIES="https://app.retriive.com")
    token = _token(priv, {"sub": "user_1"})  # no azp
    with pytest.raises(jwt.InvalidTokenError):
        auth._verify_token(token)


def test_no_allowlist_ignores_azp(monkeypatch, rsa_keys):
    priv, pub = rsa_keys
    auth = _load_auth(monkeypatch, pub)  # no CLERK_AUTHORIZED_PARTIES
    token = _token(priv, {"sub": "user_1"})
    assert auth._verify_token(token)["sub"] == "user_1"


def test_audience_enforced_when_configured(monkeypatch, rsa_keys):
    priv, pub = rsa_keys
    auth = _load_auth(monkeypatch, pub, CLERK_AUDIENCE="campusq-api")
    good = _token(priv, {"sub": "user_1", "aud": "campusq-api"})
    assert auth._verify_token(good)["sub"] == "user_1"
    bad = _token(priv, {"sub": "user_1", "aud": "some-other-api"})
    with pytest.raises(jwt.InvalidTokenError):
        auth._verify_token(bad)
