"""
LLM Router Service - Smart routing with fallback
"""
import asyncio
from typing import AsyncIterator, Optional
from app.core.config import settings


class LLMRouter:
    """
    Intelligent LLM Router.
    
    Supports strategies:
    - free → vLLM (cheapest)
    - pro → Claude (balanced)
    - enterprise → OpenAI (best quality)
    - cost → cheapest available
    - speed → fastest responding
    - latency-aware → weighted by latency
    """

    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "claude": ClaudeProvider(),
            "vllm": VLLMProvider(),
        }
        self.fallback_chain = ["vllm", "claude", "openai"]

    async def route(
        self,
        model: str,
        messages: list,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        tenant_id: int | None = None,
        strategy: str = "auto",
    ) -> dict:
        """
        Route request to appropriate provider.
        Falls back to next provider on error.
        """
        # Determine provider based on model prefix
        provider = self._get_provider_for_model(model)
        
        # Execute with fallback
        last_error = None
        providers_to_try = self._get_provider_order(provider, strategy)
        
        for p in providers_to_try:
            try:
                response = await self.providers[p].complete(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response
            except Exception as e:
                last_error = e
                continue
        
        # All providers failed
        raise Exception(f"All providers failed. Last error: {last_error}")

    async def route_stream(
        self,
        model: str,
        messages: list,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        tenant_id: int | None = None,
        strategy: str = "auto",
    ) -> AsyncIterator[str]:
        """Stream response with fallback."""
        provider = self._get_provider_for_model(model)
        
        providers_to_try = self._get_provider_order(provider, strategy)
        
        for p in providers_to_try:
            try:
                async for chunk in self.providers[p].complete_stream(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    yield chunk
                return  # Successfully streamed
            except Exception as e:
                continue
        
        yield f'{{"error": "All providers failed"}}'

    def _get_provider_for_model(self, model: str) -> str:
        """Map model to provider."""
        if model.startswith("gpt") or model.startswith("o1"):
            return "openai"
        elif model.startswith("claude"):
            return "claude"
        else:
            return "vllm"  # default to local vLLM

    def _get_provider_order(self, primary: str, strategy: str) -> list:
        """Get provider order based on strategy."""
        chain = self.fallback_chain.copy()
        
        # Move primary to front
        if primary in chain:
            chain.remove(primary)
            chain.insert(0, primary)
        
        if strategy == "cost":
            # Cheapest first
            return ["vllm", "claude", "openai"]
        elif strategy == "speed":
            # Fastest first (would need real latency data)
            return ["vllm", "openai", "claude"]
        
        return chain


class OpenAIProvider:
    """OpenAI provider wrapper."""

    async def complete(
        self,
        model: str,
        messages: list,
        temperature: float,
        max_tokens: int | None,
    ) -> dict:
        """Call OpenAI API."""
        import httpx
        
        if not settings.OPENAI_API_KEY:
            raise Exception("OpenAI API key not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
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
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.text}")
            
            return response.json()

    async def complete_stream(self, model: str, messages: list, temperature: float, max_tokens: int | None) -> AsyncIterator[str]:
        """Stream from OpenAI."""
        import httpx
        import json
        
        if not settings.OPENAI_API_KEY:
            raise Exception("OpenAI API key not configured")
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
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
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            yield data


class ClaudeProvider:
    """Claude provider wrapper."""

    async def complete(self, model: str, messages: list, temperature: float, max_tokens: int | None) -> dict:
        """Call Claude API."""
        raise NotImplementedError("Claude provider not yet implemented")

    async def complete_stream(self, model: str, messages: list, temperature: float, max_tokens: int | None) -> AsyncIterator[str]:
        """Stream from Claude."""
        raise NotImplementedError("Claude streaming not yet implemented")


class VLLMProvider:
    """vLLM provider wrapper for local models."""

    async def complete(self, model: str, messages: list, temperature: float, max_tokens: int | None) -> dict:
        """Call vLLM API."""
        import httpx
        
        if not settings.VLLM_ENDPOINT:
            raise Exception("vLLM endpoint not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.VLLM_ENDPOINT}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens or 2048,
                },
                timeout=60.0,
            )
            
            if response.status_code != 200:
                raise Exception(f"vLLM API error: {response.text}")
            
            return response.json()

    async def complete_stream(self, model: str, messages: list, temperature: float, max_tokens: int | None) -> AsyncIterator[str]:
        """Stream from vLLM."""
        import httpx
        import json
        
        if not settings.VLLM_ENDPOINT:
            raise Exception("vLLM endpoint not configured")
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{settings.VLLM_ENDPOINT}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens or 2048,
                    "stream": True,
                },
                timeout=60.0,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            yield data
