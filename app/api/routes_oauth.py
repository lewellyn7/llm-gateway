"""OAuth authentication routes."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings
from app.core.security import create_access_token
from app.services.oauth.github import GitHubOAuth
from app.services.oauth.google import GoogleOAuth
from app.services.oauth.user_handler import OAuthUserHandler

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    api_key: Optional[str] = None
    is_new_user: bool = False


def get_github_oauth() -> GitHubOAuth:
    """Get GitHub OAuth handler."""
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")
    return GitHubOAuth(
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        redirect_uri=f"{settings.APP_URL}/auth/github/callback"
    )


def get_google_oauth() -> GoogleOAuth:
    """Get Google OAuth handler."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")
    return GoogleOAuth(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        redirect_uri=f"{settings.APP_URL}/auth/google/callback"
    )


@router.get("/github")
async def github_login():
    """Redirect to GitHub OAuth authorization page."""
    oauth = get_github_oauth()
    state = oauth.generate_state()
    authorization_url = oauth.get_authorization_url(state)
    return RedirectResponse(url=authorization_url)


@router.get("/github/callback")
async def github_callback(code: str, state: Optional[str] = None):
    """Handle GitHub OAuth callback."""
    oauth = get_github_oauth()
    
    # Exchange code for token
    access_token = await oauth.get_access_token(code)
    
    # Get user info
    user_info = await oauth.get_user_info(access_token)
    
    # Auto register/login user
    result = await OAuthUserHandler.get_or_create_user(
        provider=user_info["provider"],
        provider_id=user_info["provider_id"],
        email=user_info["email"],
        name=user_info["name"],
    )
    
    # Create JWT token
    token_data = {
        "sub": user_info["email"],
        "provider": user_info["provider"],
        "provider_id": user_info["provider_id"],
        "tenant_id": result["tenant"]["id"],
    }
    jwt_token = create_access_token(token_data)
    
    return AuthResponse(
        access_token=jwt_token,
        user=result["tenant"],
        api_key=result["api_key"],
        is_new_user=result["is_new_user"],
    )


@router.get("/google")
async def google_login():
    """Redirect to Google OAuth authorization page."""
    oauth = get_google_oauth()
    state = oauth.generate_state()
    authorization_url = oauth.get_authorization_url(state)
    return RedirectResponse(url=authorization_url)


@router.get("/google/callback")
async def google_callback(code: str, state: Optional[str] = None):
    """Handle Google OAuth callback."""
    oauth = get_google_oauth()
    
    # Exchange code for token
    access_token = await oauth.get_access_token(code)
    
    # Get user info
    user_info = await oauth.get_user_info(access_token)
    
    # Auto register/login user
    result = await OAuthUserHandler.get_or_create_user(
        provider=user_info["provider"],
        provider_id=user_info["provider_id"],
        email=user_info["email"],
        name=user_info["name"],
    )
    
    # Create JWT token
    token_data = {
        "sub": user_info["email"],
        "provider": user_info["provider"],
        "provider_id": user_info["provider_id"],
        "tenant_id": result["tenant"]["id"],
    }
    jwt_token = create_access_token(token_data)
    
    return AuthResponse(
        access_token=jwt_token,
        user=result["tenant"],
        api_key=result["api_key"],
        is_new_user=result["is_new_user"],
    )


@router.get("/providers")
async def list_oauth_providers():
    """List available OAuth providers."""
    return {
        "github": {
            "available": bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET),
            "url": "/auth/github",
        },
        "google": {
            "available": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET),
            "url": "/auth/google",
        },
    }
