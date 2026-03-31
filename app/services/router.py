"""
LLM Router Service - Smart routing with fallback using Orchestrator
"""
from typing import AsyncIterator, Optional
from app.core.config import settings
from app.services.orchestrator import Orchestrator, PolicyEngine, State


class LLMRouter:
    """
    Intelligent LLM Router using Orchestrator pattern.
    
    Strategies:
    - cost_aware → vLLM (cheapest)
    - latency_aware → fastest
    - quality_aware → Claude
    - balanced → OpenAI
    """

    def __init__(self, strategy: str = "balanced"):
        self.strategy = strategy
        self.policy_engine = PolicyEngine(strategy=strategy)
        self.orchestrator = Orchestrator(
            policy_engine=self.policy_engine,
            max_iterations=5,
        )
        
        # Register provider agents
        self._register_agents()

    def _register_agents(self):
        """Register LLM provider agents."""
        self.orchestrator.register_agent("openai", self._call_openai)
        self.orchestrator.register_agent("claude", self._call_claude)
        self.orchestrator.register_agent("vllm", self._call_vllm)

    async def route(
        self,
        model: str,
        messages: list,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        tenant_id: int | None = None,
        strategy: str = "auto",
    ) -> dict:
        """Route request to appropriate provider with orchestrator."""
        # Determine provider based on model prefix
        primary_provider = self._get_provider_for_model(model)
        
        # Create initial state
        state = State(
            available_providers=["vllm", "claude", "openai"],
            current_provider=primary_provider,
            max_attempts=3,
            metadata={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "tenant_id": tenant_id,
            },
        )

        # Run orchestrator
        result_state = await self.orchestrator.run(state)
        
        if result_state.error:
            raise Exception(f"Router failed: {result_state.error}")
        
        return result_state.result

    async def route_stream(
        self,
        model: str,
        messages: list,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        tenant_id: int | None = None,
        strategy: str = "auto",
    ) -> AsyncIterator[str]:
        """Stream response with orchestrator routing."""
        primary_provider = self._get_provider_for_model(model)
        
        state = State(
            available_providers=["vllm", "claude", "openai"],
            current_provider=primary_provider,
            max_attempts=3,
            metadata={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "tenant_id": tenant_id,
            },
        )

        # Stream with fallback
        async for chunk in self._stream_with_fallback(state):
            yield chunk

    async def _stream_with_fallback(self, state: State) -> AsyncIterator[str]:
        """Stream with automatic fallback on error."""
        providers = state.available_providers
        current_idx = 0
        
        while current_idx < len(providers):
            provider = providers[current_idx]
            state.update(current_provider=provider)
            
            try:
                async for chunk in self._stream_provider(provider, state):
                    yield chunk
                return  # Success
            except Exception as e:
                current_idx += 1
                continue
        
        yield '{"error": "All providers failed"}'

    async def _stream_provider(self, provider: str, state: State) -> AsyncIterator[str]:
        """Stream from a specific provider."""
        if provider == "openai":
            async for chunk in self._call_openai_stream(state):
                yield chunk
        elif provider == "claude":
            async for chunk in self._call_claude_stream(state):
                yield chunk
        elif provider == "vllm":
            async for chunk in self._call_vllm_stream(state):
                yield chunk

    async def _call_openai(self, state: State, **kwargs) -> dict:
        """Call OpenAI API."""
        import httpx
        
        if not settings.OPENAI_API_KEY:
            raise Exception("OpenAI API key not configured")
        
        metadata = state.metadata
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": metadata["model"],
                    "messages": metadata["messages"],
                    "temperature": metadata.get("temperature", 1.0),
                    "max_tokens": metadata.get("max_tokens"),
                },
                timeout=60.0,
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.text}")
            
            return response.json()

    async def _call_openai_stream(self, state: State) -> AsyncIterator[str]:
        """Stream from OpenAI."""
        import httpx
        metadata = state.metadata
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": metadata["model"],
                    "messages": metadata["messages"],
                    "temperature": metadata.get("temperature", 1.0),
                    "max_tokens": metadata.get("max_tokens"),
                    "stream": True,
                },
                timeout=60.0,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            yield data

    async def _call_claude(self, state: State, **kwargs) -> dict:
        """Call Claude API."""
        import httpx
        
        if not settings.ANTHROPIC_API_KEY:
            raise Exception("Claude API key not configured")
        
        metadata = state.metadata
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": metadata["model"],
                    "messages": metadata["messages"],
                    "temperature": metadata.get("temperature", 1.0),
                    "max_tokens": metadata.get("max_tokens", 1024),
                },
                timeout=60.0,
            )
            
            if response.status_code != 200:
                raise Exception(f"Claude API error: {response.text}")
            
            result = response.json()
            # Convert Claude format to OpenAI format
            return {
                "id": f"claude-{result.get('id', '')}",
                "object": "chat.completion",
                "created": 1677610602,
                "model": result.get("model", metadata["model"]),
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result.get("content", [{}])[0].get("text", ""),
                    },
                    "finish_reason": "stop",
                }],
                "usage": {
                    "prompt_tokens": result.get("usage", {}).get("input_tokens", 0),
                    "completion_tokens": result.get("usage", {}).get("output_tokens", 0),
                    "total_tokens": sum(result.get("usage", {}).values()),
                },
            }

    async def _call_claude_stream(self, state: State) -> AsyncIterator[str]:
        """Stream from Claude (placeholder - Claude doesn't support streaming yet)."""
        # Claude API doesn't support streaming in the same way
        # Would need to implement chunked response
        raise Exception("Claude streaming not yet supported")

    async def _call_vllm(self, state: State, **kwargs) -> dict:
        """Call vLLM API."""
        import httpx
        
        if not settings.VLLM_ENDPOINT:
            raise Exception("vLLM endpoint not configured")
        
        metadata = state.metadata
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.VLLM_ENDPOINT}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": metadata["model"],
                    "messages": metadata["messages"],
                    "temperature": metadata.get("temperature", 1.0),
                    "max_tokens": metadata.get("max_tokens") or 2048,
                },
                timeout=60.0,
            )
            
            if response.status_code != 200:
                raise Exception(f"vLLM API error: {response.text}")
            
            return response.json()

    async def _call_vllm_stream(self, state: State) -> AsyncIterator[str]:
        """Stream from vLLM."""
        import httpx
        metadata = state.metadata
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{settings.VLLM_ENDPOINT}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": metadata["model"],
                    "messages": metadata["messages"],
                    "temperature": metadata.get("temperature", 1.0),
                    "max_tokens": metadata.get("max_tokens") or 2048,
                    "stream": True,
                },
                timeout=60.0,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            yield data

    def _get_provider_for_model(self, model: str) -> str:
        """Map model to provider."""
        if model.startswith("gpt") or model.startswith("o1"):
            return "openai"
        elif model.startswith("claude"):
            return "claude"
        else:
            return "vllm"
