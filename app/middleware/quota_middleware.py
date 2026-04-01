"""Quota middleware."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.session import AsyncSessionLocal
from app.db.crud import get_quota_by_tenant_id


class QuotaMiddleware(BaseHTTPMiddleware):
    """Middleware for quota enforcement."""

    async def dispatch(self, request: Request, call_next):
        # Skip for non-API routes
        if not request.url.path.startswith("/v1/"):
            return await call_next(request)

        # Get API key info from state (set by auth middleware)
        api_key_info = getattr(request.state, "api_key_info", None)
        if not api_key_info:
            return await call_next(request)

        tenant_id = api_key_info.get("tenant_id")
        if not tenant_id:
            return await call_next(request)

        # Check quota
        async with AsyncSessionLocal() as db:
            quota = await get_quota_by_tenant_id(db, tenant_id)

            if quota:
                # Check if quota exceeded
                if quota.used >= quota.monthly_limit:
                    raise HTTPException(
                        status_code=429,
                        detail="Monthly quota exceeded",
                        headers={
                            "X-Quota-Limit": str(quota.monthly_limit),
                            "X-Quota-Used": str(quota.used),
                            "X-Quota-Remaining": "0",
                        },
                    )

                # Add quota info to response headers
                response = await call_next(request)
                remaining = quota.monthly_limit - quota.used
                response.headers["X-Quota-Limit"] = str(quota.monthly_limit)
                response.headers["X-Quota-Used"] = str(quota.used)
                response.headers["X-Quota-Remaining"] = str(remaining)
                return response

        return await call_next(request)
