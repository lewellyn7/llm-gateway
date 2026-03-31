"""
Quota Model - Per-tenant quota management
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Quota(Base):
    """Quota configuration per tenant."""

    __tablename__ = "quotas"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), unique=True, index=True)
    monthly_token_limit: Mapped[int] = mapped_column(Integer, default=1000000)  # 1M default
    monthly_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    daily_request_limit: Mapped[int] = mapped_column(Integer, default=10000)
    daily_requests_used: Mapped[int] = mapped_column(Integer, default=0)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_soft_limit: Mapped[bool] = mapped_column(Boolean, default=True)  # soft limit allows overage with warning
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="quotas")

    def __repr__(self):
        return f"<Quota(tenant_id={self.tenant_id}, used={self.monthly_tokens_used}/{self.monthly_token_limit})>"

    def check_limit(self, tokens: int = 0, requests: int = 0) -> tuple[bool, str]:
        """
        Check if quota is exceeded.
        Returns: (allowed, message)
        """
        now = datetime.utcnow()

        # Check if we need to reset period
        if now > self.current_period_end:
            self.monthly_tokens_used = 0
            self.daily_requests_used = 0
            # Reset to next period (simplified - actual implementation needs proper period calculation)

        # Check monthly token limit
        if self.monthly_tokens_used + tokens > self.monthly_token_limit:
            if self.is_soft_limit:
                return True, "SOFT_LIMIT_EXCEEDED"
            return False, "MONTHLY_TOKEN_LIMIT_EXCEEDED"

        # Check daily request limit
        if self.daily_requests_used + requests > self.daily_request_limit:
            if self.is_soft_limit:
                return True, "SOFT_LIMIT_EXCEEDED"
            return False, "DAILY_REQUEST_LIMIT_EXCEEDED"

        return True, "OK"
