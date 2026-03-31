"""
LLM Gateway Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # App
    APP_NAME: str = "LLM Gateway"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/llm_gateway"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_RATE_LIMIT_TTL: int = 60  # seconds

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_USAGE_TOPIC: str = "llm-usage"
    KAFKA_LOG_TOPIC: str = "llm-log"
    KAFKA_BILLING_TOPIC: str = "billing-events"

    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 60  # per window
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    VLLM_ENDPOINT: Optional[str] = None

    # Model Rates (cost per 1000 tokens)
    MODEL_RATES: dict = {
        "openai": {"gpt-4o": 0.03, "gpt-4o-mini": 0.0015, "gpt-3.5-turbo": 0.002},
        "claude": {"claude-3-5-sonnet": 0.02, "claude-3-opus": 0.1},
        "vllm": {"local": 0.001},
    }

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
