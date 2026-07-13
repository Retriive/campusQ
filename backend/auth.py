"""
Clerk JWT verification for the backend API.

The Next.js frontend authenticates users with Clerk and sends the session token
as `Authorization: Bearer <token>` on backend calls. This module verifies that
token against Clerk's JWKS so the backend has a real identity boundary instead
of trusting a spoofable `user_id` form field.

Safe rollout: verification is OFF until `REQUIRE_AUTH` is set AND `CLERK_JWKS_URL`
is configured. That lets you deploy this code, set env vars, deploy the
token-sending frontend, and only then flip `REQUIRE_AUTH=true` — with no window
where prod breaks. While off, a valid token is still honored (so logs get the
real user id), but a missing/invalid token falls back to "anonymous".

Env vars:
  REQUIRE_AUTH               "true" to enforce (401 on missing/invalid token)
  CLERK_JWKS_URL             e.g. https://<your-domain>/.well-known/jwks.json
  CLERK_ISSUER               e.g. https://clerk.<your-domain>.com  (optional but recommended)
  CLERK_AUTHORIZED_PARTIES   comma-separated allowed `azp` origins (optional)
  QUALITY_GATE_KEY           shared secret for automated evals (X-Quality-Gate-Key header)
"""
import hmac
import os

from fastapi import Request, HTTPException, status

_REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "").strip().lower() in ("1", "true", "yes", "on")
_CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", "").strip()
_CLERK_ISSUER = os.getenv("CLERK_ISSUER", "").strip()
_AUTHORIZED_PARTIES = [p.strip() for p in os.getenv("CLERK_AUTHORIZED_PARTIES", "").split(",") if p.strip()]

# Lazily built so importing this module never requires network or the jwt extra
# unless verification is actually used (keeps evals/tests importing main.py cheap).
_jwk_client = None


def _get_jwk_client():
    global _jwk_client
    if _jwk_client is None:
        from jwt import PyJWKClient
        _jwk_client = PyJWKClient(_CLERK_JWKS_URL)
    return _jwk_client


def _verify_token(token: str) -> dict:
    """Verify a Clerk session JWT and return its claims. Raises on any failure."""
    import jwt

    signing_key = _get_jwk_client().get_signing_key_from_jwt(token).key
    claims = jwt.decode(
        token,
        signing_key,
        algorithms=["RS256"],
        issuer=_CLERK_ISSUER or None,
        options={"verify_iss": bool(_CLERK_ISSUER), "verify_aud": False},
    )
    if _AUTHORIZED_PARTIES:
        azp = claims.get("azp")
        if azp and azp not in _AUTHORIZED_PARTIES:
            raise jwt.InvalidTokenError("untrusted authorized party (azp)")
    return claims


def _bearer_token(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip() or None
    return None


_QUALITY_GATE_KEY = os.getenv("QUALITY_GATE_KEY", "").strip()


def _authenticated_via_quality_gate_key(request: Request) -> bool:
    supplied = request.headers.get("x-quality-gate-key", "")
    return bool(_QUALITY_GATE_KEY) and bool(supplied) and hmac.compare_digest(supplied, _QUALITY_GATE_KEY)


async def require_user(request: Request) -> str:
    """
    FastAPI dependency. Returns the authenticated Clerk user id (the `sub` claim).

    - Enforcing (REQUIRE_AUTH on + JWKS configured): 401 on missing/invalid token.
    - Not enforcing: returns the verified `sub` if a good token is present,
      otherwise "anonymous" — never blocks. This is the pre-flip state.
    """
    if _authenticated_via_quality_gate_key(request):
        return "quality-gate"

    token = _bearer_token(request)
    enforce = _REQUIRE_AUTH and bool(_CLERK_JWKS_URL)

    if not enforce:
        if token and _CLERK_JWKS_URL:
            try:
                return _verify_token(token).get("sub", "anonymous")
            except Exception:
                return "anonymous"
        return "anonymous"

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = _verify_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return claims.get("sub", "anonymous")


# ── Admin gate for internal/aggregated data endpoints ─────────────────────────
# Unlike require_user's safe-rollout default, this is DEFAULT-CLOSED: the
# dashboard endpoints expose waitlist emails and student query text, so they
# must never be public. Until ADMIN_API_KEY is set on the server, they 503.
_ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "").strip()


async def require_admin(request: Request) -> None:
    """FastAPI dependency. Grants access only with a matching X-Admin-Key header."""
    if not _ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin access is not configured. Set ADMIN_API_KEY on the server.",
        )
    supplied = request.headers.get("x-admin-key", "")
    if not supplied or not hmac.compare_digest(supplied, _ADMIN_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin key",
        )
