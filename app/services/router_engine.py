"""
Router Engine - Advanced routing with orchestrator
"""
from app.providers import OpenAIClient, ClaudeClient, VLLMClient
from app.services.orchestrator import Orchestrator, PolicyEngine, AgentResult
from app.core.config import settings


class RouterEngine:
    """
    Advanced LLM Router with Orchestrator integration.
    
    Features:
    - Multi-provider with fallback
    - Strategy-based routing (cost/latency/quality/balanced)
    - Constraint enforcement
    - Usage tracking
    """

    def __init__(self, strategy: str = "balanced"):
        self.strategy = strategy
        self.policy_engine = PolicyEngine(strategy=strategy)
        self.orchestrator = Orchestrator(
            policy_engine=self.policy_engine,
            max_iterations=10,
        )
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

        # Register orchestrator agents
        for name, client in self.providers.items():
            self.orchestrator.register_agent(name, self._create_agent(name, client))

    def _create_agent(self, name: str, client):
        """Create an agent for a provider."""
        async def agent(context: dict) -> AgentResult:
            try:
                if name == "openai":
                    response = await client.chat_completions(
                        model=context["model"],
                        messages=context["messages"],
                        temperature=context.get("temperature", 1.0),
                        max_tokens=context.get("max_tokens"),
                    )
                elif name == "claude":
                    response = await client.messages(
                        model=context["model"],
                        messages=context["messages"],
                        temperature=context.get("temperature", 1.0),
                        max_tokens=context.get("max_tokens") or 1024,
                    )
                    response = client.to_openai_format(response)
                elif name == "vllm":
                    response = await client.chat_completions(
                        model=context["model"],
                        messages=context["messages"],
                        temperature=context.get("temperature", 1.0),
                        max_tokens=context.get("max_tokens") or 2048,
                    )

                usage = response.get("usage", {})
                cost = self._calculate_cost(context["model"], usage)

                return AgentResult(
                    result=response,
                    confidence=0.95,
                    cost=cost,
                    metadata={"provider": name, "usage": usage},
                )
            except Exception as e:
                return AgentResult(
                    result=None,
                    confidence=0.0,
                    cost=0.0,
                    metadata={"error": str(e), "provider": name},
                )

        return agent

    async def chat_completion(
        self,
        model: str,
        messages: list,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        constraints: dict | None = None,
    ) -> dict:
        """Route chat completion with orchestrator."""
        provider = self._get_provider_for_model(model)

        context = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "available_providers": list(self.providers.keys()),
            "provider": provider,
            "constraints": constraints or {},
        }

        result = await self.orchestrator.run(context)

        if result.result:
            return result.result
        else:
            raise Exception(result.metadata.get("error", "All providers failed"))

    async def chat_completion_with_fallback(
        self,
        model: str,
        messages: list,
        temperature: float = 1.0,
        max_tokens: int | None = None,
    ) -> tuple[dict, str]:
        """
        Route with automatic fallback.
        Returns (response, provider_used).
        """
        provider = self._get_provider_for_model(model)
        providers = list(self.providers.keys())

        if provider in providers:
            providers.remove(provider)
            providers.insert(0, provider)

        last_error = None

        for p in providers:
            try:
                client = self.providers[p]
                
                if p == "openai":
                    response = await client.chat_completions(
                        model=model, messages=messages,
                        temperature=temperature, max_tokens=max_tokens,
                    )
                elif p == "claude":
                    response = await client.messages(
                        model=model, messages=self._convert_to_claude(messages),
                        temperature=temperature, max_tokens=max_tokens or 1024,
                    )
                    response = client.to_openai_format(response)
                elif p == "vllm":
                    response = await client.chat_completions(
                        model=model, messages=messages,
                        temperature=temperature, max_tokens=max_tokens or 2048,
                    )

                return response, p

            except Exception as e:
                last_error = e
                continue

        raise Exception(f"All providers failed: {last_error}")

    def _get_provider_for_model(self, model: str) -> str:
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

    def _convert_to_claude(self, messages: list) -> list:
        """Convert messages to Claude format."""
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

    def _calculate_cost(self, model: str, usage: dict) -> float:
        """Calculate cost for usage."""
        prompt = usage.get("prompt_tokens", 0)
        completion = usage.get("completion_tokens", 0)

        rate = 0.001  # default
        for provider, models in settings.MODEL_RATES.items():
            if model in models:
                rate = models[model]
                break

        return (prompt + completion) * rate / 1000

    def get_capabilities(self) -> dict:
        """Get router capabilities."""
        return {
            "providers": list(self.providers.keys()),
            "strategy": self.strategy,
            "streaming_support": list(self.providers.keys()),
        }
