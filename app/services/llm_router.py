"""LLM Router - Smart routing with fallback (Phase 3)."""
import json
from typing import AsyncIterator
from app.services.router_engine import RouterEngine
from app.providers.openai_client import OpenAIClient
from app.providers.claude_client import ClaudeClient
from app.providers.vllm_client import VLLMClient
from app.core.config import settings


class LLMRouter:
    """
    LLM Router - Phase 3 with Orchestrator.
    
    Features:
    - Multi-provider (OpenAI, Claude, vLLM)
    - Fallback chain
    - Strategy-based routing
    - Streaming support
    """

    def __init__(self, strategy: str = "balanced"):
        self.strategy = strategy
        self.router_engine = RouterEngine(strategy=strategy)
        self._init_providers()

    def _init_providers(self):
        """Initialize provider clients."""
        self.providers = {}

        if settings.OPENAI_API_KEY:
            self.providers["openai"] = OpenAIClient(settings.OPENAI_API_KEY)

        if settings.ANTHROPIC_API_KEY:
            self.providers["claude"] = ClaudeClient(settings.ANTHROPIC_API_KEY)

        if settings.VLLM_ENDPOINT:
            self.providers["vllm"] = VLLMClient(settings.VLLM_ENDPOINT)

        self._default_chain = ["vllm", "claude", "openai"]

    def get_provider_for_model(self, model: str) -> str:
        """Map model to provider."""
        model_lower = model.lower()

        if model_lower.startswith("gpt") or model_lower.startswith("o1"):
            return "openai"
        elif model_lower.startswith("claude"):
            return "claude"
        elif model_lower.startswith("gemini"):
            return "gemini"
        elif model_lower.startswith("deepseek"):
            return "deepseek"
        elif model_lower.startswith("moonshot"):
            return "moonshot"
        else:
            return "vllm"

    def get_provider_order(self, primary: str) -> list:
        """Get provider order based on strategy."""
        chain = self._default_chain.copy()

        if primary in chain:
            chain.remove(primary)
            chain.insert(0, primary)

        chain = [p for p in chain if p in self.providers]

        if self.strategy == "cost":
            return sorted(chain, key=lambda p: {"vllm": 1, "claude": 2, "openai": 3}.get(p, 99))
        elif self.strategy == "latency":
            return sorted(chain, key=lambda p: {"vllm": 1, "openai": 2, "claude": 3}.get(p, 99))
        elif self.strategy == "quality":
            return sorted(chain, key=lambda p: {"claude": 1, "openai": 2, "vllm": 3}.get(p, 99))

        return chain

    async def chat_completion(
        self,
        model: str,
        messages: list,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> dict:
        """Route chat completion to appropriate provider with fallback."""
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
                    claude_messages = self._convert_to_claude_format(messages)
                    result = await self.providers["claude"].messages(
                        model=model, messages=claude_messages,
                        temperature=temperature, max_tokens=max_tokens or 1024,
                    )
                    return self.providers["claude"].to_openai_format(result)
                elif p == "vllm":
                    return await self.providers["vllm"].chat_completions(
                        model=model, messages=messages,
                        temperature=temperature, max_tokens=max_tokens or 2048, stream=stream,
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
                elif p == "claude":
                    # Claude doesn't support streaming in same format
                    # Fallback to non-streaming
                    claude_messages = self._convert_to_claude_format(messages)
                    result = await self.providers["claude"].messages(
                        model=model, messages=claude_messages,
                        temperature=temperature, max_tokens=max_tokens or 1024,
                    )
                    formatted = self.providers["claude"].to_openai_format(result)
                    # Yield as a single chunk
                    yield f"data: {json.dumps(formatted)}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                elif p == "vllm":
                    async for chunk in self.providers["vllm"].chat_completions_stream(
                        model=model, messages=messages,
                        temperature=temperature, max_tokens=max_tokens or 2048,
                    ):
                        yield chunk
                    return
            except Exception as e:
                print(f"Provider {p} failed, trying fallback: {e}")
                continue

        yield json.dumps({"error": {"message": "All providers failed", "type": "internal_error"}})

    def _convert_to_claude_format(self, messages: list) -> list:
        """Convert OpenAI messages to Claude format."""
        claude_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                claude_messages.append({
                    "role": "user",
                    "content": f"[System] {msg.get('content', '')}"
                })
            else:
                claude_messages.append({
                    "role": "user" if role == "user" else "assistant",
                    "content": msg.get("content", ""),
                })
        return claude_messages

    def list_available_providers(self) -> list:
        """List available providers."""
        return list(self.providers.keys())

    def get_capabilities(self) -> dict:
        """Get provider capabilities."""
        return {
            "providers": self.list_available_providers(),
            "streaming": ["openai", "vllm"],
            "models": {
                "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                "claude": ["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku"],
                "vllm": ["llama-3-70b", "llama-3-8b", "qwen-72b"],
            },
            "strategy": self.strategy,
        }
