"""OAuth authentication routes."""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings
from app.core.security import create_access_token
from app.services.oauth.github import GitHubOAuth
from app.services.oauth.google import GoogleOAuth

router = APIRouter(prefix="/auth", tags=["auth"])


class OAuthCallback(BaseModel):
    code: str
    state: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


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
    
    # Create JWT token
    token_data = {
        "sub": user_info["email"],
        "provider": user_info["provider"],
        "provider_id": user_info["provider_id"],
    }
    jwt_token = create_access_token(token_data)
    
    return AuthResponse(
        access_token=jwt_token,
        user=user_info
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
    
    # Create JWT token
    token_data = {
        "sub": user_info["email"],
        "provider": user_info["provider"],
        "provider_id": user_info["provider_id"],
    }
    jwt_token = create_access_token(token_data)
    
    return AuthResponse(
        access_token=jwt_token,
        user=user_info
    )


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing cookie."""
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}
