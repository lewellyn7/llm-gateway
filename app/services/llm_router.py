"""LLM Router - Smart routing with fallback."""
from typing import AsyncIterator
from app.providers import OpenAIClient, ClaudeClient, VLLMClient
from app.core.config import settings


class LLMRouter:
    """
    Intelligent LLM Router.
    
    Routes requests to appropriate providers with fallback.
    Strategies: cost, latency, quality, balanced
    """

    def __init__(self, strategy: str = "balanced"):
        self.strategy = strategy
        self.providers = {
            "openai": OpenAIClient(),
            "claude": ClaudeClient(),
            "vllm": VLLMClient(),
        }
        self.fallback_chain = ["vllm", "claude", "openai"]

    def get_provider_for_model(self, model: str) -> str:
        """Map model to provider."""
        if model.startswith("gpt") or model.startswith("o1"):
            return "openai"
        elif model.startswith("claude"):
            return "claude"
        return "vllm"

    def get_provider_order(self, primary: str) -> list:
        """Get provider order based on strategy."""
        chain = self.fallback_chain.copy()
        if primary in chain:
            chain.remove(primary)
            chain.insert(0, primary)
        
        if self.strategy == "cost":
            return ["vllm", "claude", "openai"]
        elif self.strategy == "latency":
            return ["vllm", "openai", "claude"]
        return chain

    async def chat_completion(
        self,
        model: str,
        messages: list,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> dict:
        """Route chat completion request."""
        provider = self.get_provider_for_model(model)
        order = self.get_provider_order(provider)
        last_error = None

        for p in order:
            try:
                if p == "openai":
                    return await self.providers["openai"].chat_completions(
                        model=model, messages=messages,
                        temperature=temperature, max_tokens=max_tokens, stream=stream,
                    )
                elif p == "claude":
                    result = await self.providers["claude"].messages(
                        model=model, messages=messages,
                        temperature=temperature, max_tokens=max_tokens or 1024,
                    )
                    return self.providers["claude"].to_openai_format(result)
                elif p == "vllm":
                    return await self.providers["vllm"].chat_completions(
                        model=model, messages=messages,
                        temperature=temperature, max_tokens=max_tokens, stream=stream,
                    )
            except Exception as e:
                last_error = e
                continue

        raise Exception(f"All providers failed. Last error: {last_error}")

    async def chat_completion_stream(
        self,
        model: str,
        messages: list,
        temperature: float = 1.0,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Stream chat completion with fallback."""
        provider = self.get_provider_for_model(model)
        order = self.get_provider_order(provider)

        for p in order:
            try:
                if p == "openai":
                    async for chunk in self.providers["openai"].chat_completions_stream(
                        model=model, messages=messages,
                        temperature=temperature, max_tokens=max_tokens,
                    ):
                        yield chunk
                    return
                elif p == "vllm":
                    async for chunk in self.providers["vllm"].chat_completions_stream(
                        model=model, messages=messages,
                        temperature=temperature, max_tokens=max_tokens,
                    ):
                        yield chunk
                    return
            except Exception:
                continue

        yield '{"error": "All providers failed"}'
