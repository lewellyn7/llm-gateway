"""GitHub OAuth handler."""

from urllib.parse import urlencode
from app.services.oauth.base import OAuthProvider


class GitHubOAuth(OAuthProvider):
    """GitHub OAuth 2.0 provider."""

    AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_URL = "https://api.github.com/user"
    EMAIL_URL = "https://api.github.com/user/emails"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        super().__init__(client_id, client_secret, redirect_uri)

    def get_authorization_url(self, state: str) -> str:
        """Get GitHub OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email",
            "state": state,
        }
        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def get_access_token(self, code: str) -> str:
        """Exchange code for access token."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        result = await self.exchange_code_for_token(self.TOKEN_URL, data)
        return result.get("access_token", "")

    async def get_user_info(self, access_token: str) -> dict:
        """Get user info from GitHub."""
        user_data = await self.get_json(self.USER_URL, access_token)

        # Get primary email
        emails = await self.get_json(self.EMAIL_URL, access_token)
        primary_email = next(
            (e["email"] for e in emails if e.get("primary") and e.get("verified")),
            user_data.get("email", ""),
        )

        return {
            "provider": "github",
            "provider_id": str(user_data.get("id", "")),
            "username": user_data.get("login", ""),
            "name": user_data.get("name", user_data.get("login", "")),
            "email": primary_email,
            "avatar_url": user_data.get("avatar_url", ""),
            "bio": user_data.get("bio", ""),
        }
