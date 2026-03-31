"""
Billing Service - Token cost calculation and logging
"""
from app.core.config import settings
from app.core.kafka import kafka_producer


class BillingService:
    """Service for calculating and logging billing information."""

    @staticmethod
    def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate cost for token usage.
        Cost = tokens * rate / 1000
        """
        total_tokens = prompt_tokens + completion_tokens
        
        # Find provider rate
        rate = 0.001  # default rate
        
        for provider, models in settings.MODEL_RATES.items():
            if model in models:
                rate = models[model]
                break
        
        return total_tokens * rate / 1000

    @staticmethod
    async def log_usage(
        tenant_id: int,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        status: str,
        error_message: str | None = None,
    ):
        """Log usage to Kafka for async processing."""
        cost = BillingService.calculate_cost(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        
        await kafka_producer.log_usage(
            tenant_id=str(tenant_id),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            status=status,
        )
        
        # Log billing event if there's cost
        if cost > 0:
            await kafka_producer.log_billing_event(
                tenant_id=str(tenant_id),
                amount=cost,
                currency="USD",
                event_type="usage_charge",
            )

    @staticmethod
    def get_model_rate(model: str) -> float:
        """Get the rate for a specific model."""
        for provider, models in settings.MODEL_RATES.items():
            if model in models:
                return models[model]
        return 0.001  # default
