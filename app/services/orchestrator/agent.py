"""
Agent - Constrained execution unit
"""
from dataclasses import dataclass
from typing import Any, Generic, TypeVar
from abc import ABC, abstractmethod


T = TypeVar("T")


@dataclass
class AgentResult:
    """Structured result from agent execution."""
    result: Any          # The actual result
    confidence: float    # 0.0-1.0 confidence score
    cost: float          # Execution cost (tokens, money, time)
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        # Clamp confidence
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass
class AgentContext:
    """Context passed to agents - immutable constraints."""
    model: str
    messages: list
    temperature: float = 1.0
    max_tokens: int | None = None
    budget: float | None = None
    max_latency_ms: float | None = None
    allowed_providers: list[str] | None = None
    strategy: str = "balanced"
    tenant_id: int | None = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Agent(ABC):
    """
    Base Agent class.
    
    Agents execute within strict constraints.
    They CANNOT output freely - must return structured AgentResult.
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    @abstractmethod
    async def run(
        self,
        context: AgentContext,
    ) -> AgentResult:
        """
        Execute agent with constraints.
        
        Must return structured AgentResult:
        - result: the output (constrained by max_tokens)
        - confidence: 0.0-1.0 confidence score
        - cost: execution cost
        """
        pass

    def validate_context(self, context: AgentContext) -> tuple[bool, str]:
        """
        Validate context constraints before execution.
        Returns (valid, error_message).
        """
        if context.budget is not None and context.budget <= 0:
            return False, "Budget exhausted"
        
        if context.max_latency_ms is not None and context.max_latency_ms <= 0:
            return False, "Max latency exceeded"
        
        return True, ""


class ChatAgent(Agent):
    """Chat completion agent."""

    def __init__(self, provider: str = "openai"):
        super().__init__(
            name=f"chat_{provider}",
            description=f"Chat completion via {provider}",
        )
        self.provider = provider

    async def run(self, context: AgentContext) -> AgentResult:
        """Execute chat completion within constraints."""
        # Validate
        valid, error = self.validate_context(context)
        if not valid:
            return AgentResult(
                result=None,
                confidence=0.0,
                cost=0.0,
                metadata={"error": error},
            )

        from app.services.router import LLMRouter
        
        router = LLMRouter(strategy=context.strategy)
        
        try:
            response = await router.route(
                model=context.model,
                messages=context.messages,
                temperature=context.temperature,
                max_tokens=context.max_tokens,
                tenant_id=context.tenant_id,
            )
            
            # Extract usage for cost calculation
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            # Calculate cost
            from app.services.billing import BillingService
            cost = BillingService.calculate_cost(
                model=context.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
            
            # Calculate confidence based on response quality
            choices = response.get("choices", [])
            finish_reason = choices[0].get("finish_reason", "unknown") if choices else "unknown"
            confidence = 1.0 if finish_reason == "stop" else 0.5
            
            return AgentResult(
                result=response,
                confidence=confidence,
                cost=cost,
                metadata={
                    "provider": self.provider,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                },
            )
            
        except Exception as e:
            return AgentResult(
                result=None,
                confidence=0.0,
                cost=0.0,
                metadata={"error": str(e), "provider": self.provider},
            )


class RouterAgent(Agent):
    """Routing decision agent."""

    def __init__(self):
        super().__init__(
            name="router",
            description="Routes requests to appropriate providers",
        )

    async def run(self, context: AgentContext) -> AgentResult:
        """Decide routing based on strategy and constraints."""
        from app.services.orchestrator.policy import PolicyEngine
        
        policy = PolicyEngine(strategy=context.strategy)
        
        # Determine provider based on model
        model = context.model
        if model.startswith("gpt") or model.startswith("o1"):
            provider = "openai"
        elif model.startswith("claude"):
            provider = "claude"
        else:
            provider = "vllm"
        
        # Check if provider is allowed
        if context.allowed_providers and provider not in context.allowed_providers:
            # Fallback to allowed provider
            provider = context.allowed_providers[0]
        
        return AgentResult(
            result={"provider": provider, "model": model},
            confidence=1.0,
            cost=0.0,  # Routing is free
            metadata={"strategy": context.strategy},
        )


class BillingAgent(Agent):
    """Billing calculation agent."""

    def __init__(self):
        super().__init__(
            name="billing", 
            description="Calculates and logs billing",
        )

    async def run(self, context: AgentContext) -> AgentResult:
        """Calculate billing for the request."""
        from app.services.billing import BillingService
        
        # This would be called post-request
        # For now, return zero cost placeholder
        return AgentResult(
            result={"cost": 0.0, "currency": "USD"},
            confidence=1.0,
            cost=0.0,
            metadata={"agent": "billing"},
        )


# Registry of available agents
AGENT_REGISTRY: dict[str, type[Agent]] = {
    "chat_openai": lambda: ChatAgent("openai"),
    "chat_claude": lambda: ChatAgent("claude"),
    "chat_vllm": lambda: ChatAgent("vllm"),
    "router": lambda: RouterAgent(),
    "billing": lambda: BillingAgent(),
}


def get_agent(name: str) -> Agent | None:
    """Get agent by name from registry."""
    factory = AGENT_REGISTRY.get(name)
    return factory() if factory else None
