"""
API Key Model - Per-tenant API keys with model restrictions
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class APIKey(Base):
    """API Key model."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    allowed_models: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated or JSON
    rate_limit: Mapped[int] = mapped_column(default=60)  # requests per minute
    daily_limit: Mapped[int | None] = mapped_column(nullable=True)  # per day
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"

    def is_valid(self) -> bool:
        """Check if key is valid."""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def allowed_for_model(self, model: str) -> bool:
        """Check if model is allowed for this key."""
        if not self.allowed_models:
            return True  # All models allowed
        # Parse allowed models (could be JSON or comma-separated)
        allowed = self.allowed_models
        if model in allowed.split(","):
            return True
        return False
