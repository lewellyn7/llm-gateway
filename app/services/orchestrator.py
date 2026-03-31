"""
Orchestrator - Agent execution with state management
"""
from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum


class ActionType(Enum):
    AGENT = "agent"
    TOOL = "tool"
    ROUTE = "route"
    FALLBACK = "fallback"
    END = "end"


@dataclass
class Action:
    type: ActionType
    name: str
    params: dict = field(default_factory=dict)
    priority: int = 0


@dataclass
class AgentResult:
    """Structured result from agent execution."""
    result: Any
    confidence: float
    cost: float
    metadata: dict = field(default_factory=dict)


@dataclass
class State:
    """Represents the current execution state."""
    done: bool = False
    error: str | None = None
    attempt_count: int = 0
    max_attempts: int = 3
    current_provider: str | None = None
    available_providers: list = field(default_factory=list)
    result: Any = None
    metadata: dict = field(default_factory=dict)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class PolicyEngine:
    """
    Policy engine for routing decisions.
    Strategies: cost, latency, quality, balanced
    """

    def __init__(self, strategy: str = "balanced"):
        self.strategy = strategy

    def decide(self, state: State) -> Action:
        if state.done:
            return Action(type=ActionType.END, name="end")

        if state.error and state.attempt_count < state.max_attempts:
            return Action(
                type=ActionType.FALLBACK,
                name="fallback_provider",
                params={"attempt": state.attempt_count + 1},
            )

        return Action(
            type=ActionType.ROUTE,
            name="route",
            params={"provider": self._get_next_provider(state)},
        )

    def _get_next_provider(self, state: State) -> str:
        providers = state.available_providers
        if not providers:
            return state.current_provider or "openai"

        if state.current_provider and state.current_provider in providers:
            idx = providers.index(state.current_provider)
            if idx + 1 < len(providers):
                return providers[idx + 1]

        return providers[0]


class Orchestrator:
    """
    Orchestrator for managing agent execution.
    
    Pattern:
    while not state.done():
        action = policy_engine.decide(state)
        result = await execute_action(action, state)
        update(state, result)
        enforce_constraints(state)
    """

    def __init__(
        self,
        policy_engine: PolicyEngine | None = None,
        max_iterations: int = 10,
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        self.max_iterations = max_iterations
        self.agents: dict[str, Callable] = {}
        self.tools: dict[str, Callable] = {}
        self.constraints: list[Callable] = []

    def register_agent(self, name: str, agent: Callable):
        self.agents[name] = agent

    def register_tool(self, name: str, tool: Callable):
        self.tools[name] = tool

    def add_constraint(self, constraint: Callable):
        self.constraints.append(constraint)

    async def run(self, context: dict) -> AgentResult:
        """Run orchestrator with context."""
        state = State(
            available_providers=context.get("available_providers", ["vllm", "claude", "openai"]),
            current_provider=context.get("provider", "openai"),
            max_attempts=context.get("max_attempts", 3),
            metadata=context,
        )

        iteration = 0
        total_cost = 0.0

        while not state.done and iteration < self.max_iterations:
            iteration += 1
            state.update(attempt_count=iteration)

            action = self.policy_engine.decide(state)
            result = await self._execute_action(action, state)

            if result:
                total_cost += result.cost
                state.metadata["total_cost"] = total_cost

                if not result.metadata.get("error"):
                    state.update(done=True, result=result.result)
                else:
                    state.update(error=result.metadata.get("error"))

            if not self._enforce_constraints(state):
                state.update(done=True, error="Constraint violation")

        return AgentResult(
            result=state.result,
            confidence=0.8 if state.done else 0.0,
            cost=total_cost,
            metadata={"iterations": iteration, "error": state.error},
        )

    async def _execute_action(self, action: Action, state: State) -> AgentResult | None:
        try:
            if action.type == ActionType.ROUTE:
                provider = action.params.get("provider")
                state.update(current_provider=provider)
                return AgentResult(result={"provider": provider}, confidence=1.0, cost=0.0)

            elif action.type == ActionType.FALLBACK:
                providers = state.available_providers
                current = state.current_provider
                if current in providers:
                    idx = providers.index(current)
                    if idx + 1 < len(providers):
                        next_provider = providers[idx + 1]
                        state.update(current_provider=next_provider)
                        return AgentResult(
                            result={"fallback_to": next_provider},
                            confidence=0.8,
                            cost=0.0,
                        )
                return AgentResult(result=None, confidence=0.0, cost=0.0, metadata={"error": "No more providers"})

            elif action.type == ActionType.END:
                state.update(done=True)
                return AgentResult(result={"completed": True}, confidence=1.0, cost=0.0)

        except Exception as e:
            return AgentResult(result=None, confidence=0.0, cost=0.0, metadata={"error": str(e)})

        return None

    def _enforce_constraints(self, state: State) -> bool:
        for constraint in self.constraints:
            try:
                if not constraint(state):
                    return False
            except Exception:
                return False
        return True


# Built-in constraints
def max_budget_constraint(budget: float) -> Callable:
    def constraint(state: State) -> bool:
        return state.metadata.get("total_cost", 0) <= budget
    return constraint


def max_latency_constraint(max_ms: float) -> Callable:
    def constraint(state: State) -> bool:
        return state.metadata.get("latency_ms", 0) <= max_ms
    return constraint


def provider_whitelist(allowed: list[str]) -> Callable:
    def constraint(state: State) -> bool:
        if state.current_provider:
            return state.current_provider in allowed
        return True
    return constraint
