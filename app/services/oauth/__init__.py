"""OAuth service module."""
from app.services.oauth.github import GitHubOAuth
from app.services.oauth.google import GoogleOAuth

__all__ = ["GitHubOAuth", "GoogleOAuth"]
