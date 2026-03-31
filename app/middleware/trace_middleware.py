"""Trace middleware for request tracing."""

import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class TraceMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracing with correlation ID."""

    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        start_time = time.time()

        request.state.trace_id = trace_id
        request.state.start_time = start_time

        response = await call_next(request)

        # Add trace headers to response
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Response-Time"] = (
            f"{(time.time() - start_time) * 1000:.2f}ms"
        )

        return response
