"""Base OAuth handler."""

from abc import ABC, abstractmethod
import httpx


class OAuthProvider(ABC):
    """Abstract base class for OAuth providers."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        """Get the authorization URL to redirect users to."""
        pass

    @abstractmethod
    async def get_access_token(self, code: str) -> str:
        """Exchange authorization code for access token."""
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> dict:
        """Get user information using the access token."""
        pass

    def generate_state(self) -> str:
        """Generate a random state parameter for CSRF protection."""
        import secrets

        return secrets.token_urlsafe(32)

    async def exchange_code_for_token(self, token_url: str, data: dict) -> dict:
        """Generic token exchange."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers={"Accept": "application/json"},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_json(self, url: str, access_token: str) -> dict:
        """Generic JSON GET request with auth."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
