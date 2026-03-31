"""Security utilities."""

import hashlib
import secrets
from jose import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Header
from typing import Optional
from app.core.config import settings


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a new API key."""
    return f"sk-{secrets.token_urlsafe(32)}"


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify JWT token."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


async def verify_api_key(authorization: Optional[str] = Header(None)) -> dict | None:
    """Verify API key from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    api_key = authorization[7:]
    hashlib.sha256(api_key.encode()).hexdigest()
    # TODO: Query database for API key
    return {"tenant_id": 1, "api_key_id": 1, "name": "default", "plan": "free"}
