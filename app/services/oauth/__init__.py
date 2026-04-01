"""OAuth service module."""

from app.services.oauth.base import OAuthProvider
from app.services.oauth.github import GitHubOAuth
from app.services.oauth.google import GoogleOAuth
from app.services.oauth.user_handler import OAuthUserHandler

__all__ = ["OAuthProvider", "GitHubOAuth", "GoogleOAuth", "OAuthUserHandler"]
