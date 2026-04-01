"""Google OAuth handler."""

from urllib.parse import urlencode
from app.services.oauth.base import OAuthProvider


class GoogleOAuth(OAuthProvider):
    """Google OAuth 2.0 provider."""

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        super().__init__(client_id, client_secret, redirect_uri)

    def get_authorization_url(self, state: str) -> str:
        """Get Google OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "online",
            "state": state,
        }
        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def get_access_token(self, code: str) -> str:
        """Exchange code for access token."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        result = await self.exchange_code_for_token(self.TOKEN_URL, data)
        return result.get("access_token", "")

    async def get_user_info(self, access_token: str) -> dict:
        """Get user info from Google."""
        user_data = await self.get_json(self.USER_URL, access_token)

        return {
            "provider": "google",
            "provider_id": str(user_data.get("id", "")),
            "username": user_data.get("email", "").split("@")[0],
            "name": user_data.get("name", ""),
            "email": user_data.get("email", ""),
            "avatar_url": user_data.get("picture", ""),
            "bio": "",
        }
