"""Billing service."""
from app.core.config import settings


class BillingService:
    """Calculate and log billing."""

    @staticmethod
    def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for token usage."""
        total_tokens = prompt_tokens + completion_tokens
        rate = 0.001  # default

        for provider, models in settings.MODEL_RATES.items():
            if model in models:
                rate = models[model]
                break

        return total_tokens * rate / 1000
