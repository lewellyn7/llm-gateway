"""
Policy Engine - Decides which action to take based on state
"""
from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, Awaitable


class ActionType(Enum):
    """Types of actions an orchestrator can take."""
    AGENT = "agent"
    TOOL = "tool"
    ROUTE = "route"
    FALLBACK = "fallback"
    END = "end"


@dataclass
class Action:
    """Represents an action to be taken."""
    type: ActionType
    name: str
    params: dict = None
    priority: int = 0

    def __post_init__(self):
        if self.params is None:
            self.params = {}


class PolicyEngine:
    """
    Policy engine for deciding actions based on state.
    
    Strategies:
    - cost_aware: Prefer cheaper models
    - latency_aware: Prefer faster models
    - quality_aware: Prefer better models
    - balanced: Balance cost and quality
    """

    def __init__(self, strategy: str = "balanced"):
        self.strategy = strategy

    def decide(self, state: dict) -> Action:
        """
        Decide the next action based on current state.
        
        State should contain:
        - available_providers: list of available LLM providers
        - current_provider: current provider being used
        - attempt_count: number of attempts made
        - error: last error if any
        - budget: remaining budget
        - latency_requirements: latency constraints
        """
        # Check if we should end
        if state.get("done"):
            return Action(type=ActionType.END, name="end")

        # Handle errors - try fallback
        if state.get("error"):
            return self._handle_error(state)

        # Route based on strategy
        return self._route_based_on_strategy(state)

    def _handle_error(self, state: dict) -> Action:
        """Handle error by trying fallback or escalating."""
        attempt = state.get("attempt_count", 0)
        max_attempts = state.get("max_attempts", 3)
        
        if attempt < max_attempts:
            # Try next provider in fallback chain
            return Action(
                type=ActionType.FALLBACK,
                name="fallback_provider",
                params={"attempt": attempt + 1},
            )
        else:
            # Max attempts reached, end
            return Action(type=ActionType.END, name="max_attempts_exceeded")

    def _route_based_on_strategy(self, state: dict) -> Action:
        """Route based on configured strategy."""
        providers = state.get("available_providers", [])
        
        if not providers:
            return Action(type=ActionType.END, name="no_providers")

        if self.strategy == "cost_aware":
            # Prefer cheapest (vLLM first)
            return Action(
                type=ActionType.ROUTE,
                name="route_to_cheapest",
                params={"provider": self._get_cheapest_provider(providers)},
            )
        elif self.strategy == "latency_aware":
            # Prefer fastest
            return Action(
                type=ActionType.ROUTE,
                name="route_to_fastest",
                params={"provider": self._get_fastest_provider(providers)},
            )
        elif self.strategy == "quality_aware":
            # Prefer best quality
            return Action(
                type=ActionType.ROUTE,
                name="route_to_best_quality",
                params={"provider": self._get_best_quality_provider(providers)},
            )
        else:  # balanced
            return Action(
                type=ActionType.ROUTE,
                name="route_balanced",
                params={"provider": providers[0] if providers else None},
            )

    def _get_cheapest_provider(self, providers: list) -> str:
        """Get cheapest provider."""
        costs = {"vllm": 0.001, "claude": 0.02, "openai": 0.03}
        return min(providers, key=lambda p: costs.get(p, 0.1))

    def _get_fastest_provider(self, providers: list) -> str:
        """Get fastest provider (would use real latency data in production)."""
        # vLLM typically fastest for local models
        order = ["vllm", "openai", "claude"]
        for p in order:
            if p in providers:
                return p
        return providers[0]

    def _get_best_quality_provider(self, providers: list) -> str:
        """Get best quality provider."""
        # Claude typically best for complex tasks
        order = ["claude", "openai", "vllm"]
        for p in order:
            if p in providers:
                return p
        return providers[0]
