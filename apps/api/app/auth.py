"""Fail-closed Supabase access-token verification.

Tenant identity is read only from verified JWT app_metadata. Never accept tenant IDs
from query parameters, request bodies, or unverified token payloads.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, PyJWTError


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    tenant_id: str
    claims: dict[str, Any]


def _auth_settings() -> tuple[str, str, str]:
    project_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    issuer = os.getenv("SUPABASE_JWT_ISSUER", f"{project_url}/auth/v1" if project_url else "")
    jwks_url = os.getenv(
        "SUPABASE_JWKS_URL",
        f"{project_url}/auth/v1/.well-known/jwks.json" if project_url else "",
    )
    audience = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")
    if not issuer or not jwks_url:
        raise RuntimeError("Supabase JWT verification is not configured")
    return issuer, jwks_url, audience


@lru_cache(maxsize=4)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=300)


def verify_access_token(token: str) -> dict[str, Any]:
    """Verify signature, issuer, expiry and audience against configured Supabase JWKS."""
    issuer, jwks_url, audience = _auth_settings()
    signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        issuer=issuer,
        audience=audience,
        options={"require": ["exp", "iss", "sub", "aud"]},
    )
    if not isinstance(claims.get("sub"), str) or not claims["sub"]:
        raise PyJWTError("Token subject is missing")
    return claims


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    """Resolve a verified principal and its server-issued tenant claim."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = verify_access_token(credentials.credentials)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication provider is not configured",
        ) from exc
    except (PyJWTError, Exception) as exc:
        # Auth failures must never fall back to trusting client-supplied identity.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    app_metadata = claims.get("app_metadata")
    tenant_id = app_metadata.get("tenant_id") if isinstance(app_metadata, dict) else None
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user has no tenant assignment",
        )
    return AuthenticatedUser(user_id=claims["sub"], tenant_id=tenant_id, claims=claims)
