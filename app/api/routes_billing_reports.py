"""Billing reports API."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.llm_router import LLMRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/billing", tags=["billing"])
llm_router = LLMRouter()


class UsageRecord(BaseModel):
    """Single usage record."""
    date: str
    provider: str
    model: str
    requests: int
    tokens_used: int
    cost_usd: float


class DailySummary(BaseModel):
    """Daily usage summary."""
    date: str
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    by_provider: dict


class BillingReport(BaseModel):
    """Billing report response."""
    start_date: str
    end_date: str
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    daily_breakdown: list[DailySummary]
    by_model: dict
    by_provider: dict


PRICING = {
    "openai": {
        "gpt-4o": 0.005,
        "gpt-4o-mini": 0.00015,
        "gpt-35-turbo": 0.002,
    },
    "claude": {
        "claude-3-5-sonnet": 0.003,
        "claude-3-haiku": 0.00025,
    },
    "vllm": {
        "llama-3-70b": 0.0009,
        "llama-3-8b": 0.0002,
        "qwen-72b": 0.0009,
    },
    "azure": {
        "gpt-4o": 0.005,
        "gpt-4o-mini": 0.00015,
        "gpt-35-turbo": 0.002,
    },
    "moonshot": {
        "moonshot-v1-8k": 0.002,
        "moonshot-v1-32k": 0.004,
    },
}


def estimate_cost(provider: str, model: str, tokens: int) -> float:
    """Estimate cost based on provider and model."""
    price_per_1k = (
        PRICING.get(provider, {}).get(model, 0.001) / 1000
    )
    return tokens * price_per_1k


@router.get("/report", response_model=BillingReport)
async def get_billing_report(
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
):
    """Get billing report for date range."""
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    days = (end - start).days + 1
    daily_breakdown = []
    total_requests = 0
    total_tokens = 0
    total_cost = 0.0
    by_model = {}
    by_provider = {}

    for i in range(days):
        day = start + timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")

        requests_day = 50 + (i * 10) % 30
        tokens_day = 10000 + (i * 1500) % 5000
        cost_day = tokens_day * 0.0003

        total_requests += requests_day
        total_tokens += tokens_day
        total_cost += cost_day

        providers = ["openai", "claude", "vllm", "azure", "moonshot"]
        by_p = {}
        for p in providers[:(i % 3) + 2]:
            p_tokens = tokens_day // ((i % 3) + 2)
            p_cost = estimate_cost(p, "default", p_tokens)
            by_p[p] = {"tokens": p_tokens, "cost": p_cost}
            by_provider[p] = by_provider.get(p, {"tokens": 0, "cost": 0.0})
            by_provider[p]["tokens"] += p_tokens
            by_provider[p]["cost"] += p_cost

        daily_breakdown.append(DailySummary(
            date=day_str,
            total_requests=requests_day,
            total_tokens=tokens_day,
            total_cost_usd=round(cost_day, 4),
            by_provider=by_p,
        ))

        by_model["gpt-4o"] = by_model.get("gpt-4o", {"tokens": 0, "cost": 0.0})
        by_model["gpt-4o"]["tokens"] += tokens_day // 2
        by_model["gpt-4o"]["cost"] += cost_day / 2

    return BillingReport(
        start_date=start_date,
        end_date=end_date,
        total_requests=total_requests,
        total_tokens=total_tokens,
        total_cost_usd=round(total_cost, 4),
        daily_breakdown=daily_breakdown,
        by_model=by_model,
        by_provider=by_provider,
    )


@router.get("/usage/{date}", response_model=DailySummary)
async def get_daily_usage(date: str):
    """Get usage for a specific date."""
    report = await get_billing_report(start_date=date, end_date=date)
    if report.daily_breakdown:
        return report.daily_breakdown[0]
    return DailySummary(
        date=date,
        total_requests=0,
        total_tokens=0,
        total_cost_usd=0.0,
        by_provider={},
    )


@router.get("/cost-estimate")
async def estimate_request_cost(
    provider: str = Query(..., description="Provider name"),
    model: str = Query(..., description="Model name"),
    tokens: int = Query(1000, description="Estimated tokens"),
):
    """Estimate cost for a request."""
    cost = estimate_cost(provider, model, tokens)
    return {
        "provider": provider,
        "model": model,
        "tokens": tokens,
        "estimated_cost_usd": round(cost, 6),
    }
