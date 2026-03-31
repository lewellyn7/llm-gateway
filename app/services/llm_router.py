"""LLM Router - Multi-Provider Smart Routing."""
import json
from typing import AsyncIterator
from app.providers.openai_client import OpenAIClient
from app.providers.claude_client import ClaudeClient
from app.providers.vllm_client import VLLMClient
from app.core.config import settings


class LLMRouter:
    """
    Intelligent LLM Router with multi-provider support.
    
    Providers:
    - openai: GPT-4, GPT-3.5
    - claude: Claude 3 Opus, Sonnet, Haiku
    - vllm: Local models (Llama, Qwen, etc.)
    
    Strategies:
    - cost: Prefer cheapest
    - latency: Prefer fastest
    - quality: Prefer best quality
    - balanced: Balance cost and quality
    """

    def __init__(self, strategy: str = "balanced"):
        self.strategy = strategy
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

        # Default provider order
        self._default_chain = ["vllm", "claude", "openai"]

    def get_provider_for_model(self, model: str) -> str:
        """Map model to provider."""
        model_lower = model.lower()

        if model_lower.startswith("gpt") or model_lower.startswith("o1"):
            return "openai"
        elif model_lower.startswith("claude"):
            return "claude"
        elif model_lower.startswith("gemini"):
            return "gemini"  # Placeholder
        elif model_lower.startswith("deepseek"):
            return "deepseek"  # Placeholder
        elif model_lower.startswith("moonshot"):
            return "moonshot"  # Placeholder
        else:
            return "vllm"

    def get_provider_order(self, primary: str) -> list:
        """Get provider fallback order based on strategy."""
        chain = self._default_chain.copy()

        # Move primary to front if available
        if primary in chain:
            chain.remove(primary)
            chain.insert(0, primary)

        # Filter to only available providers
        chain = [p for p in chain if p in self.providers]

        # Adjust based on strategy
        if self.strategy == "cost":
            # Sort by cost (vllm cheapest, then claude, then openai)
            return sorted(chain, key=lambda p: {"vllm": 1, "claude": 2, "openai": 3}.get(p, 99))
        elif self.strategy == "latency":
            # vLLM typically fastest, then OpenAI, then Claude
            return sorted(chain, key=lambda p: {"vllm": 1, "openai": 2, "claude": 3}.get(p, 99))
        elif self.strategy == "quality":
            # Claude best, then OpenAI, then vLLM
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
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=stream,
                    )
                elif p == "claude":
                    # Convert messages format for Claude
                    claude_messages = self._convert_to_claude_format(messages)
                    result = await self.providers["claude"].messages(
                        model=model,
                        messages=claude_messages,
                        temperature=temperature,
                        max_tokens=max_tokens or 1024,
                    )
                    return self.providers["claude"].to_openai_format(result)
                elif p == "vllm":
                    return await self.providers["vllm"].chat_completions(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens or 2048,
                        stream=stream,
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
        """Stream chat completion with provider fallback."""
        provider = self.get_provider_for_model(model)
        order = self.get_provider_order(provider)

        for p in order:
            try:
                if p == "openai":
                    async for chunk in self.providers["openai"].chat_completions_stream(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ):
                        yield chunk
                    return
                elif p == "claude":
                    # Claude streaming - convert to OpenAI format
                    claude_messages = self._convert_to_claude_format(messages)
                    async for chunk in self.providers["claude"].messages(
                        model=model,
                        messages=claude_messages,
                        temperature=temperature,
                        max_tokens=max_tokens or 1024,
                        stream=True,
                    ):
                        yield chunk
                    return
                elif p == "vllm":
                    async for chunk in self.providers["vllm"].chat_completions_stream(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens or 2048,
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
            # Claude uses "user" and "assistant", not "system"
            if role == "system":
                # Claude puts system messages in a special field, but we can prepend
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
            "streaming": ["openai", "vllm", "claude"],
            "models": {
                "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                "claude": ["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku"],
                "vllm": ["llama-3-70b", "llama-3-8b", "qwen-72b"],
            },
            "strategy": self.strategy,
        }
