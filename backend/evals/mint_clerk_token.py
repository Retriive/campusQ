#!/usr/bin/env python3
"""
Mint a short-lived Clerk session JWT for automated quality gates.

Uses the Clerk Backend API so CI can authenticate against production without
storing an expiring session token in GitHub secrets.

Env:
  CLERK_SECRET_KEY          Required — Clerk secret key (sk_test_... or sk_live_...)
  CAMPUSQ_GATE_USER_EMAIL   Optional — defaults to quality-gate@retriive.com

Prints the JWT to stdout (for shell capture). Exit 2 on setup errors.
"""

from __future__ import annotations

import os
import sys

import requests

CLERK_API = "https://api.clerk.com/v1"
DEFAULT_EMAIL = "quality-gate@retriive.com"


def _headers(secret: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {secret}",
        "Content-Type": "application/json",
    }


def _find_user_id(secret: str, email: str) -> str | None:
    resp = requests.get(
        f"{CLERK_API}/users",
        headers=_headers(secret),
        params={"email_address": [email], "limit": 1},
        timeout=30,
    )
    resp.raise_for_status()
    for user in resp.json():
        for addr in user.get("email_addresses", []):
            if addr.get("email_address", "").lower() == email.lower():
                return user["id"]
    return None


def _create_user(secret: str, email: str) -> str:
    resp = requests.post(
        f"{CLERK_API}/users",
        headers=_headers(secret),
        json={
            "email_address": [email],
            "password": os.urandom(24).hex(),
            "skip_password_checks": True,
            "skip_password_requirement": True,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _create_session(secret: str, user_id: str) -> str:
    resp = requests.post(
        f"{CLERK_API}/sessions",
        headers=_headers(secret),
        json={"user_id": user_id},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _mint_jwt(secret: str, session_id: str) -> str:
    resp = requests.post(
        f"{CLERK_API}/sessions/{session_id}/tokens",
        headers=_headers(secret),
        json={"expires_in_seconds": 300},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("jwt") or data.get("token")
    if not token:
        raise RuntimeError(f"Clerk token response missing jwt: {data}")
    return token


def mint_clerk_session_token() -> str:
    secret = os.getenv("CLERK_SECRET_KEY", "").strip()
    if not secret:
        raise RuntimeError("CLERK_SECRET_KEY is required to mint a quality-gate token.")

    email = os.getenv("CAMPUSQ_GATE_USER_EMAIL", DEFAULT_EMAIL).strip()
    user_id = _find_user_id(secret, email) or _create_user(secret, email)
    session_id = _create_session(secret, user_id)
    return _mint_jwt(secret, session_id)


def main() -> int:
    try:
        print(mint_clerk_session_token())
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
