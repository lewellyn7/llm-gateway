"""Usage tracking middleware."""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.kafka import kafka_producer


class UsageMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking API usage."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        # Log usage after response
        latency_ms = (time.time() - start_time) * 1000

        if hasattr(request.state, "api_key_info") and request.state.api_key_info:
            tenant_id = str(request.state.api_key_info.get("tenant_id", ""))
        else:
            tenant_id = "anonymous"

        await kafka_producer.log_request(
            tenant_id=tenant_id,
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            latency_ms=latency_ms,
        )

        return response
