"""Azure OpenAI API client."""

from typing import AsyncIterator, Optional
import httpx
from app.core.config import settings


class AzureOpenAIClient:
    """Azure OpenAI API client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_version: str = "2024-02-01",
    ):
        self.api_key = api_key or settings.AZURE_OPENAI_API_KEY
        self.endpoint = endpoint or settings.AZURE_OPENAI_ENDPOINT
        self.api_version = api_version

        if not self.endpoint:
            raise ValueError("Azure OpenAI endpoint is required")

    def _get_headers(self) -> dict:
        """Get request headers."""
        return {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

    async def chat_completions(
        self,
        model: str,
        messages: list,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> dict:
        """Send chat completion request."""
        url = f"{self.endpoint}/openai/deployments/{model}/chat/completions?api-version={self.api_version}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": stream,
                },
                headers=self._get_headers(),
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()

    async def chat_completions_stream(
        self,
        model: str,
        messages: list,
        temperature: float = 1.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream chat completion responses."""
        url = f"{self.endpoint}/openai/deployments/{model}/chat/completions?api-version={self.api_version}"

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                url,
                json={
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
                headers=self._get_headers(),
                timeout=60.0,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            yield "data: [DONE]\n\n"
                        else:
                            yield f"data: {data}\n\n"

    async def embeddings(
        self,
        input_text: str,
        model: str = "text-embedding-ada-002",
    ) -> dict:
        """Get embeddings for text."""
        url = f"{self.endpoint}/openai/deployments/{model}/embeddings?api-version={self.api_version}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"input": input_text},
                headers=self._get_headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
