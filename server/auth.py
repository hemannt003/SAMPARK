"""
Authentication helpers — JWT tokens, password hashing, middleware.

Auth is *optional* (controlled by settings.enable_auth).  When disabled
every request is treated as an anonymous session.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

import hashlib
import hmac
import secrets

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.config import get_settings
from server.database import User, get_db

settings = get_settings()

# ── Password hashing (PBKDF2-SHA256 — no C dependency issues) ──

_HASH_ALGO = "pbkdf2_sha256"
_ITERATIONS = 260_000  # OWASP recommended for SHA-256


def hash_password(plain: str) -> str:
    """Hash a password with PBKDF2-SHA256 + random salt."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), _ITERATIONS)
    return f"{_HASH_ALGO}${_ITERATIONS}${salt}${dk.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against a PBKDF2-SHA256 hash."""
    try:
        _, iterations_str, salt, stored_hash = hashed.split("$")
        iterations = int(iterations_str)
        dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), iterations)
        return hmac.compare_digest(dk.hex(), stored_hash)
    except (ValueError, AttributeError):
        return False


# ── JWT ─────────────────────────────────────────────────────────

def create_access_token(user_id: int, phone: str) -> str:
    """Create a signed JWT for the given user."""
    payload = {
        "sub": str(user_id),
        "phone": phone,
        "exp": dt.datetime.utcnow() + dt.timedelta(minutes=settings.jwt_expire_minutes),
        "iat": dt.datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT. Raises HTTPException on failure."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ── FastAPI dependency ──────────────────────────────────────────
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    If auth is enabled, extract user from JWT bearer token.
    If auth is disabled, return None (anonymous).
    """
    if not settings.enable_auth:
        return None

    if credentials is None:
        return None

    payload = decode_access_token(credentials.credentials)
    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user


async def require_user(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """Dependency that *requires* an authenticated user."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user
