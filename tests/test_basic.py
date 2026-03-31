"""Basic tests for LLM Gateway."""

import pytest


def test_imports():
    """Test that core modules can be imported."""
    from app.core.config import settings

    assert settings.APP_NAME == "LLM Gateway"
    assert settings is not None


def test_settings():
    """Test settings configuration."""
    from app.core.config import Settings

    s = Settings()
    assert s.APP_NAME == "LLM Gateway"
    assert s.PORT == 8000


def test_hash_api_key():
    """Test API key hashing."""
    from app.core.security import hash_api_key, generate_api_key

    key = generate_api_key()
    assert key.startswith("sk-")

    hashed = hash_api_key(key)
    assert len(hashed) == 64  # SHA256 hex length


def test_create_access_token():
    """Test JWT token creation."""
    from app.core.security import create_access_token

    token = create_access_token({"sub": "test"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_billing_calculation():
    """Test billing calculation."""
    from app.services.billing import BillingService

    cost = BillingService.calculate_cost(
        model="gpt-4o",
        prompt_tokens=1000,
        completion_tokens=500,
    )

    # gpt-4o rate: 0.03 per 1000 tokens
    # total: 1500 tokens
    # cost: 1500 * 0.03 / 1000 = 0.045
    assert cost == 0.045


def test_tool_registry():
    """Test tool registry."""
    from app.services.tools import tool_registry

    tools = tool_registry.list_tools()
    assert len(tools) > 0
    assert any(t["function"]["name"] == "get_weather" for t in tools)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
