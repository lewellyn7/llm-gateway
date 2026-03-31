"""Admin routes for dashboard."""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.core.security import create_access_token

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


class LoginRequest(BaseModel):
    username: str
    password: str


class TenantCreate(BaseModel):
    name: str
    email: str
    password: str
    plan: str = "free"


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: LoginRequest):
    """Admin login."""
    # Simple admin check (in production, use proper auth)
    if request.username == "admin" and request.password == "admin":
        token = create_access_token({"sub": "admin", "role": "admin"})
        return {"status": "success", "token": token}

    # Check tenant credentials
    # TODO: Implement proper tenant auth
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Admin dashboard."""
    return templates.TemplateResponse("admin.html", {"request": request})


@router.get("/api/admin/stats")
async def admin_stats():
    """Get dashboard stats."""
    # Placeholder - would query database
    return {
        "tenants": 1,
        "api_keys": 3,
        "requests_today": 1523,
        "monthly_cost": "45.67",
    }


@router.get("/api/admin/tenants")
async def list_tenants():
    """List all tenants."""
    return [
        {"id": 1, "name": "Default", "email": "admin@example.com", "plan": "enterprise", "is_active": True},
    ]


@router.get("/api/admin/keys")
async def list_keys():
    """List all API keys."""
    return [
        {"id": 1, "name": "Production", "key_masked": "sk-xxxx...xxxx", "tenant_name": "Default", "rate_limit": 60, "is_active": True},
        {"id": 2, "name": "Development", "key_masked": "sk-xxxx...xxxx", "tenant_name": "Default", "rate_limit": 30, "is_active": True},
    ]


@router.get("/api/admin/usage")
async def admin_usage():
    """Get usage stats."""
    return {
        "total_requests": 45678,
        "total_tokens": 1234567,
        "by_model": {
            "gpt-4o": 12345,
            "claude-3-5-sonnet": 9876,
            "gpt-3.5-turbo": 5432,
        },
        "by_provider": {
            "openai": 20000,
            "anthropic": 15000,
            "vllm": 10678,
        },
    }


@router.post("/api/admin/settings")
async def save_settings(settings_data: dict):
    """Save system settings."""
    # In production, would save to database or config file
    return {"status": "success"}


@router.post("/api/admin/tenants")
async def create_tenant(tenant: TenantCreate):
    """Create a new tenant."""
    return {"id": 2, "name": tenant.name, "email": tenant.email, "plan": tenant.plan, "is_active": True}


@router.delete("/api/admin/keys/{key_id}")
async def revoke_key(key_id: int):
    """Revoke an API key."""
    return {"status": "success"}
