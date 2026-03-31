"""Configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "LLM Gateway"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/llm_gateway"
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT_TTL: int = 60
    RATE_LIMIT_REQUESTS: int = 60

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_USAGE_TOPIC: str = "llm-usage"
    KAFKA_LOG_TOPIC: str = "llm-log"
    KAFKA_BILLING_TOPIC: str = "billing-events"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    VLLM_ENDPOINT: Optional[str] = None

    MODEL_RATES: dict = {
        "openai": {"gpt-4o": 0.03, "gpt-4o-mini": 0.0015},
        "claude": {"claude-3-5-sonnet": 0.02},
        "vllm": {"local": 0.001},
    }


settings = Settings()
