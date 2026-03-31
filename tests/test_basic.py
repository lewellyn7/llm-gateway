"""
Basic tests for LLM Gateway
"""
import pytest


def test_imports():
    """Test that all modules can be imported."""
    from app.core.config import settings
    from app.core.database import Base
    from app.models import Tenant, APIKey, UsageRecord, Quota
    
    assert settings.APP_NAME == "LLM Gateway"
    assert settings is not None


def test_tenant_model():
    """Test Tenant model structure."""
    from app.models.tenant import Tenant
    
    assert Tenant.__tablename__ == "tenants"
    assert hasattr(Tenant, "id")
    assert hasattr(Tenant, "name")
    assert hasattr(Tenant, "email")
    assert hasattr(Tenant, "plan")


def test_api_key_model():
    """Test APIKey model structure."""
    from app.models.api_key import APIKey
    
    assert APIKey.__tablename__ == "api_keys"
    assert hasattr(APIKey, "tenant_id")
    assert hasattr(APIKey, "key_hash")
    assert hasattr(APIKey, "is_valid")


def test_billing_calculation():
    """Test billing calculation."""
    from app.services.billing import BillingService
    
    cost = BillingService.calculate_cost(
        model="gpt-4o",
        prompt_tokens=1000,
        completion_tokens=500,
    )
    
    # gpt-4o rate: 0.03 per 1000 tokens
    # total tokens: 1500
    # cost: 1500 * 0.03 / 1000 = 0.045
    assert cost == 0.045


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
