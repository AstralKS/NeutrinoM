"""FastAPI dependencies for authentication.

Provides JWT-based auth using Supabase tokens.
Supports both ES256 (asymmetric) and HS256 (symmetric) token verification.
"""

import logging
from typing import Annotated

import jwt
from jwt import PyJWKClient
from fastapi import Depends, Header, HTTPException, status

from advisor.config import get_settings

logger = logging.getLogger(__name__)

# ── JWKS client (cached, fetches public keys from Supabase) ──
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    """Lazily create and cache the JWKS client for Supabase."""
    global _jwks_client
    if _jwks_client is None:
        settings = get_settings()
        jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
        print(f"[AUTH] Initialized JWKS client: {jwks_url}", flush=True)
    return _jwks_client


class AuthenticatedUser:
    """Represents an authenticated Supabase user."""

    def __init__(self, id: str, email: str | None = None, provider: str | None = None, access_token: str | None = None):
        self.id = id
        self.email = email
        self.provider = provider
        self.access_token = access_token  # The raw JWT for proxying

    def __repr__(self) -> str:
        return f"AuthenticatedUser(id={self.id}, email={self.email})"


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthenticatedUser:
    """Verify the Supabase JWT from the Authorization header.

    Supports both ES256 (via JWKS) and HS256 (via JWT secret) verification.

    Args:
        authorization: Bearer token from the Authorization header.

    Returns:
        AuthenticatedUser with id and email.

    Raises:
        HTTPException 401 if token is missing, invalid, or expired.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header. Expected: Bearer <token>",
        )

    token = authorization.removeprefix("Bearer ").strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    try:
        # Peek at the token header to determine the algorithm
        unverified_header = jwt.get_unverified_header(token)
        token_alg = unverified_header.get("alg", "HS256")

        if token_alg.startswith("ES") or token_alg.startswith("RS") or token_alg.startswith("PS"):
            # Asymmetric algorithm — use JWKS public key
            jwks_client = _get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[token_alg],
                audience="authenticated",
            )
        else:
            # Symmetric (HMAC) algorithm — use JWT secret
            settings = get_settings()
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256", "HS384", "HS512"],
                audience="authenticated",
            )

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )

        logger.info(f"Authenticated user: {user_id} ({email})")
        return AuthenticatedUser(
            id=user_id,
            email=email,
            provider=payload.get("app_metadata", {}).get("provider"),
            access_token=token,
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT validation failed: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {type(e).__name__}",
        )


async def get_optional_user(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthenticatedUser | None:
    """Same as get_current_user but returns None if no auth header.

    Use this for endpoints that work for both authenticated and anonymous users.
    """
    if not authorization:
        return None

    try:
        return await get_current_user(authorization)
    except HTTPException:
        # Silently return None for optional auth — don't block anonymous users
        return None
