"""Embeddings client."""
import httpx
from app.core.config import settings


class EmbeddingsClient:
    """OpenAI-compatible embeddings client."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.OPENAI_API_KEY

    async def create(
        self,
        input: str | list,
        model: str = "text-embedding-3-small",
    ) -> dict:
        """Create embeddings."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"input": input, "model": model},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
