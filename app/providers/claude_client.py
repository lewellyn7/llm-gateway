"""Claude client."""
import httpx
from typing import AsyncIterator
from app.core.config import settings


class ClaudeClient:
    """Claude API client."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.base_url = "https://api.anthropic.com/v1"

    async def messages(
        self,
        model: str,
        messages: list,
        temperature: float = 1.0,
        max_tokens: int = 1024,
    ) -> dict:
        """Create a message."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()

    def to_openai_format(self, claude_response: dict) -> dict:
        """Convert Claude response to OpenAI format."""
        return {
            "id": f"claude-{claude_response.get('id', '')}",
            "object": "chat.completion",
            "created": 1677610602,
            "model": claude_response.get("model", ""),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": claude_response.get("content", [{}])[0].get("text", ""),
                },
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": claude_response.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": claude_response.get("usage", {}).get("output_tokens", 0),
                "total_tokens": sum(claude_response.get("usage", {}).values()),
            },
        }
