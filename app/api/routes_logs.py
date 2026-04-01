"""Log query interface API."""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/logs", tags=["logs"])


class LogLevel(str, Enum):
    """Log level enum."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry(BaseModel):
    """Single log entry."""

    timestamp: str
    level: str
    service: str
    message: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None


class LogQueryResponse(BaseModel):
    """Log query response."""

    total: int
    page: int
    page_size: int
    logs: list[LogEntry]


MOCK_SERVICES = ["llm-gateway", "api-gateway", "auth-service", "billing-service"]
MOCK_MESSAGES = [
    "Chat completion request received",
    "Provider response received",
    "Streaming chunk sent",
    "Rate limit check passed",
    "Authentication successful",
    "Request completed successfully",
]


def generate_mock_logs(
    start_time: datetime,
    end_time: datetime,
    level: Optional[str] = None,
    service: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
) -> list[LogEntry]:
    """Generate mock log entries for demonstration."""
    logs = []
    delta = end_time - start_time
    num_logs = min(limit, max(50, int(delta.total_seconds()) // 60))

    import random

    random.seed(42)

    for i in range(num_logs):
        offset = timedelta(seconds=i * delta.total_seconds() / num_logs)
        ts = start_time + offset
        log_level = random.choice(["INFO", "INFO", "INFO", "WARNING", "ERROR"])
        svc = random.choice(MOCK_SERVICES)
        msg = random.choice(MOCK_MESSAGES)

        entry = LogEntry(
            timestamp=ts.isoformat(),
            level=log_level,
            service=svc,
            message=msg,
            request_id=f"req_{random.randint(100000, 999999)}",
            user_id=f"user_{random.randint(1, 100)}",
            model=random.choice(["gpt-4o", "claude-3-5-sonnet", "llama-3-70b"]),
            provider=random.choice(["openai", "claude", "vllm"]),
            duration_ms=random.randint(50, 5000),
            tokens_used=random.randint(100, 4000) if random.random() > 0.3 else None,
        )

        if level and entry.level != level:
            continue
        if service and entry.service != service:
            continue
        if search and search.lower() not in entry.message.lower():
            continue

        logs.append(entry)

    return logs


@router.get("/query", response_model=LogQueryResponse)
async def query_logs(
    start_time: Optional[str] = Query(None, description="Start time ISO format"),
    end_time: Optional[str] = Query(None, description="End time ISO format"),
    level: Optional[str] = Query(None, description="Log level filter"),
    service: Optional[str] = Query(None, description="Service name filter"),
    search: Optional[str] = Query(None, description="Search in message"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    model: Optional[str] = Query(None, description="Filter by model"),
    request_id: Optional[str] = Query(None, description="Filter by request ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
):
    """Query logs with filters."""
    if not start_time:
        start_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    if not end_time:
        end_time = datetime.utcnow().isoformat()

    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time)

    all_logs = generate_mock_logs(start, end, level, service, search, limit=500)

    if user_id:
        all_logs = [log for log in all_logs if log.user_id == user_id]
    if model:
        all_logs = [log for log in all_logs if log.model == model]
    if request_id:
        all_logs = [log for log in all_logs if log.request_id == request_id]

    total = len(all_logs)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    logs = all_logs[start_idx:end_idx]

    return LogQueryResponse(
        total=total,
        page=page,
        page_size=page_size,
        logs=logs,
    )


@router.get("/stats")
async def get_log_stats(
    start_time: Optional[str] = Query(None, description="Start time ISO format"),
    end_time: Optional[str] = Query(None, description="End time ISO format"),
):
    """Get log statistics for the time period."""
    if not start_time:
        start_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    if not end_time:
        end_time = datetime.utcnow().isoformat()

    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time)

    logs = generate_mock_logs(start, end, limit=200)

    level_counts = {}
    service_counts = {}
    model_counts = {}
    total_duration = 0
    total_tokens = 0

    for log in logs:
        level_counts[log.level] = level_counts.get(log.level, 0) + 1
        service_counts[log.service] = service_counts.get(log.service, 0) + 1
        if log.model:
            model_counts[log.model] = model_counts.get(log.model, 0) + 1
        if log.duration_ms:
            total_duration += log.duration_ms
        if log.tokens_used:
            total_tokens += log.tokens_used

    return {
        "start_time": start_time,
        "end_time": end_time,
        "total_logs": len(logs),
        "by_level": level_counts,
        "by_service": service_counts,
        "by_model": model_counts,
        "avg_duration_ms": total_duration // len(logs) if logs else 0,
        "total_tokens": total_tokens,
    }


@router.get("/{request_id}")
async def get_log_by_request_id(request_id: str):
    """Get all logs for a specific request ID."""
    logs = generate_mock_logs(
        datetime.utcnow() - timedelta(days=1),
        datetime.utcnow(),
        limit=500,
    )
    filtered = [log for log in logs if log.request_id == request_id]
    return {"request_id": request_id, "logs": filtered}
