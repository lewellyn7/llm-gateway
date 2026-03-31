"""Claude client with streaming support."""
import httpx
from typing import AsyncIterator
from app.core.config import settings


class ClaudeClient:
    """Claude API client with streaming support."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.base_url = "https://api.anthropic.com/v1"

    async def messages(
        self,
        model: str,
        messages: list,
        temperature: float = 1.0,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> dict | AsyncIterator[str]:
        """Create a message or stream."""
        if stream:
            return self._stream_messages(model, messages, temperature, max_tokens)
        
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

    async def _stream_messages(
        self,
        model: str,
        messages: list,
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[str]:
        """Stream message response as SSE."""
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
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
                    "stream": True,
                },
                timeout=60.0,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                    elif line.startswith("data:"):
                        data = line[5:].strip()
                        if data == "[DONE]":
                            yield "data: [DONE]\n\n"
                        else:
                            # Convert Claude event to OpenAI-compatible format
                            try:
                                import json
                                event_data = json.loads(data)
                                openai_chunk = self._to_openai_chunk(event_data, event_type)
                                if openai_chunk:
                                    yield f"data: {json.dumps(openai_chunk)}\n\n"
                            except json.JSONDecodeError:
                                yield f"data: {data}\n\n"

    def _to_openai_chunk(self, event: dict, event_type: str) -> dict | None:
        """Convert Claude streaming event to OpenAI format."""
        if event_type == "message_start":
            return {
                "id": f"chatcmpl-{event.get('message', {}).get('id', '')}",
                "object": "chat.completion.chunk",
                "created": 1677610602,
                "model": event.get("message", {}).get("model", ""),
                "choices": [{"index": 0, "delta": {}, "finish_reason": None}],
            }
        elif event_type == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                return {
                    "choices": [{
                        "index": 0,
                        "delta": {"content": delta.get("text", "")},
                        "finish_reason": None,
                    }]
                }
        elif event_type == "message_stop":
            return None  # Handled by [DONE]
        return None

    def to_openai_format(self, claude_response: dict) -> dict:
        """Convert Claude response to OpenAI format."""
        content = ""
        if claude_response.get("content"):
            for block in claude_response["content"]:
                if block.get("type") == "text":
                    content = block.get("text", "")

        return {
            "id": f"claude-{claude_response.get('id', '')}",
            "object": "chat.completion",
            "created": 1677610602,
            "model": claude_response.get("model", ""),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": claude_response.get("stop_reason", "stop"),
            }],
            "usage": {
                "prompt_tokens": claude_response.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": claude_response.get("usage", {}).get("output_tokens", 0),
                "total_tokens": sum(claude_response.get("usage", {}).values()),
            },
        }
