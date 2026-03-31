"""Authentication middleware."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import verify_api_key
from app.core.limiter import rate_limiter


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication."""

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Check API key
        auth = request.headers.get("authorization")
        api_key_info = await verify_api_key(auth)

        if not api_key_info and request.url.path.startswith("/v1/"):
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Check rate limit
        if api_key_info:
            allowed, remaining, reset = await rate_limiter.is_allowed(
                f"rate:{auth}",
                limit=60,
                window=60,
            )
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={"X-RateLimit-Remaining": str(remaining)},
                )

        request.state.api_key_info = api_key_info
        return await call_next(request)
