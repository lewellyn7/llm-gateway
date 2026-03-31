"""
Authentication Service - API Key verification
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Header

from app.core.redis import redis_client
from app.core.config import settings


async def verify_api_key(authorization: Optional[str] = Header(None)) -> dict | None:
    """
    Verify API key from Authorization header.
    Returns tenant info if valid, None otherwise.
    
    Format: Bearer sk-xxxxx
    """
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    api_key = authorization[7:]  # Remove "Bearer " prefix
    
    # Check rate limit first
    if settings.RATE_LIMIT_ENABLED:
        allowed, remaining, reset = await redis_client.sliding_window_rate_limit(
            f"rate:{api_key}",
            settings.RATE_LIMIT_REQUESTS,
            settings.RATE_LIMIT_WINDOW,
        )
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_REQUESTS),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset),
                },
            )
    
    # In production, verify against database
    # For now, return mock tenant info
    # TODO: Query database for API key hash
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Mock return - would check DB in production
    return {
        "tenant_id": 1,
        "api_key_id": 1,
        "name": "default",
        "plan": "free",
        "rate_limit": settings.RATE_LIMIT_REQUESTS,
    }


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a new API key."""
    return f"sk-{secrets.token_urlsafe(32)}"


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    from jose import jwt
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt
