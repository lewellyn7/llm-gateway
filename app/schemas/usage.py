"""Usage schemas."""

from pydantic import BaseModel, ConfigDict
from datetime import datetime


class UsageRecord(BaseModel):
    id: int
    tenant_id: int
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    latency_ms: float
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsageStats(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost: float
    by_model: dict
    by_provider: dict
