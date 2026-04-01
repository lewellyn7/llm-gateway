"""Admin API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/admin", tags=["admin"])


class TenantCreate(BaseModel):
    name: str
    email: str
    plan: str = "free"


class TenantResponse(BaseModel):
    id: int
    name: str
    email: str
    plan: str
    is_active: bool
    created_at: str


class APIKeyCreate(BaseModel):
    tenant_id: int
    name: Optional[str] = None


class APIKeyResponse(BaseModel):
    id: int
    key: str
    key_prefix: str
    tenant_id: int
    tenant_name: str
    created_at: str
    is_active: bool


class QuotaResponse(BaseModel):
    tenant_id: int
    tenant_name: str
    monthly_limit: int
    used: int
    remaining: int
    reset_at: str
    plan: str


# In-memory demo data
TENANTS = [
    {"id": 1, "name": "文杨科技", "email": "wy@example.com", "plan": "pro", "is_active": True, "created_at": "2026-03-01"}
]
API_KEYS = [
    {"id": 1, "key": "sk-demo-abc123", "key_prefix": "sk-demo", "tenant_id": 1, "tenant_name": "文杨科技", "created_at": "2026-03-01", "is_active": True}
]
QUOTAS = {
    1: {"tenant_id": 1, "tenant_name": "文杨科技", "monthly_limit": 100000, "used": 4567, "remaining": 95433, "reset_at": "2026-04-01", "plan": "pro"}
}


def get_next_tenant_id():
    return max([t["id"] for t in TENANTS], default=0) + 1


def get_next_key_id():
    return max([k["id"] for k in API_KEYS], default=0) + 1


@router.get("/stats")
async def get_stats():
    """Get dashboard stats."""
    return {
        "tenants": len(TENANTS),
        "api_keys": len(API_KEYS),
        "requests_today": 1234,
        "monthly_cost": "23.45"
    }


@router.get("/tenants")
async def list_tenants():
    """List all tenants."""
    return TENANTS


@router.post("/tenants")
async def create_tenant(data: TenantCreate):
    """Create a new tenant."""
    tenant = {
        "id": get_next_tenant_id(),
        "name": data.name,
        "email": data.email,
        "plan": data.plan,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    }
    TENANTS.append(tenant)
    
    # Create default quota based on plan
    limits = {"free": 10000, "pro": 100000, "enterprise": 1000000}
    QUOTAS[tenant["id"]] = {
        "tenant_id": tenant["id"],
        "tenant_name": tenant["name"],
        "monthly_limit": limits.get(data.plan, 10000),
        "used": 0,
        "remaining": limits.get(data.plan, 10000),
        "reset_at": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d"),
        "plan": data.plan
    }
    
    return tenant


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: int):
    """Delete a tenant."""
    global TENANTS, API_KEYS, QUOTAS
    TENANTS = [t for t in TENANTS if t["id"] != tenant_id]
    API_KEYS = [k for k in API_KEYS if k["tenant_id"] != tenant_id]
    if tenant_id in QUOTAS:
        del QUOTAS[tenant_id]
    return {"message": "Tenant deleted"}


@router.get("/keys")
async def list_keys():
    """List all API keys."""
    return API_KEYS


@router.post("/keys")
async def create_key(data: APIKeyCreate):
    """Create a new API key."""
    import secrets
    key = f"sk-{secrets.token_urlsafe(32)}"
    tenant = next((t for t in TENANTS if t["id"] == data.tenant_id), None)
    
    api_key = {
        "id": get_next_key_id(),
        "key": key,
        "key_prefix": key[:12],
        "tenant_id": data.tenant_id,
        "tenant_name": tenant["name"] if tenant else "Unknown",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "is_active": True
    }
    API_KEYS.append(api_key)
    return api_key


@router.delete("/keys/{key_id}")
async def revoke_key(key_id: int):
    """Revoke an API key."""
    global API_KEYS
    for key in API_KEYS:
        if key["id"] == key_id:
            key["is_active"] = False
            return {"message": "Key revoked"}
    raise HTTPException(status_code=404, detail="Key not found")


@router.get("/quotas")
async def list_quotas():
    """List all quotas."""
    return list(QUOTAS.values())


@router.get("/quotas/{tenant_id}")
async def get_tenant_quota(tenant_id: int):
    """Get quota for a specific tenant."""
    if tenant_id not in QUOTAS:
        raise HTTPException(status_code=404, detail="Quota not found")
    return QUOTAS[tenant_id]


@router.put("/quotas/{tenant_id}")
async def update_quota(tenant_id: int, monthly_limit: int):
    """Update quota limit for a tenant."""
    if tenant_id not in QUOTAS:
        raise HTTPException(status_code=404, detail="Quota not found")
    QUOTAS[tenant_id]["monthly_limit"] = monthly_limit
    QUOTAS[tenant_id]["remaining"] = monthly_limit - QUOTAS[tenant_id]["used"]
    return QUOTAS[tenant_id]


@router.get("/usage")
async def get_usage():
    """Get usage summary."""
    return {
        "summary": {
            "total_requests": 45678,
            "total_tokens": 1234567,
            "total_cost": "234.56",
            "by_provider": {"openai": 0.6, "claude": 0.3, "vllm": 0.1},
            "by_model": {"gpt-4o": 0.4, "claude-3-5-sonnet": 0.3, "llama-3-70b": 0.3}
        }
    }


@router.post("/settings")
async def update_settings(settings: dict):
    """Update system settings."""
    return {"message": "Settings updated"}
