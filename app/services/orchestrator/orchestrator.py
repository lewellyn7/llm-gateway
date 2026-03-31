"""
Orchestrator - Executes agents and tools with state management
"""
from typing import Any, Callable, Awaitable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from app.services.orchestrator.policy import PolicyEngine, Action, ActionType


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
        """Update state fields."""
        for key, value in kwargs.items():
            setattr(self, key, value)


@dataclass
class AgentResult:
    """Result from an agent execution."""
    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict = field(default_factory=dict)


class Orchestrator:
    """
    Orchestrator for managing agent and tool execution.
    
    Executes a loop:
    1. Policy engine decides next action
    2. Execute action (agent or tool)
    3. Update state
    4. Enforce constraints
    5. Repeat until done or max iterations
    """

    def __init__(
        self,
        policy_engine: PolicyEngine | None = None,
        max_iterations: int = 10,
    ):
        self.policy_engine = policy_engine or PolicyEngine(strategy="balanced")
        self.max_iterations = max_iterations
        self.agents: dict[str, Callable[..., Awaitable[Any]]] = {}
        self.tools: dict[str, Callable[..., Awaitable[Any]]] = {}
        self.constraints: list[Callable[[State], bool]] = []

    def register_agent(self, name: str, agent: Callable[..., Awaitable[Any]]):
        """Register an agent callable."""
        self.agents[name] = agent

    def register_tool(self, name: str, tool: Callable[..., Awaitable[Any]]):
        """Register a tool callable."""
        self.tools[name] = tool

    def add_constraint(self, constraint: Callable[[State], bool]):
        """Add a constraint function. Returns True if constraint is satisfied."""
        self.constraints.append(constraint)

    async def run(self, initial_state: dict | State) -> State:
        """
        Run the orchestrator with initial state.
        
        State should contain:
        - available_providers: list of providers
        - task: the task to execute
        - context: execution context
        """
        if isinstance(initial_state, dict):
            state = State(**initial_state)
        else:
            state = initial_state

        iteration = 0
        
        while not state.done and iteration < self.max_iterations:
            iteration += 1
            state.update(attempt_count=iteration)

            # 1. Policy engine decides action
            action = self.policy_engine.decide(state.__dict__)

            # 2. Execute action
            result = await self._execute_action(action, state)

            # 3. Update state with result
            self._update_state(state, action, result)

            # 4. Enforce constraints
            if not self._enforce_constraints(state):
                state.update(done=True, error="Constraint violation")

        return state

    async def _execute_action(self, action: Action, state: State) -> AgentResult:
        """Execute a single action."""
        try:
            if action.type == ActionType.AGENT:
                if action.name in self.agents:
                    data = await self.agents[action.name](state, **action.params)
                    return AgentResult(success=True, data=data)
                return AgentResult(success=False, error=f"Unknown agent: {action.name}")

            elif action.type == ActionType.TOOL:
                if action.name in self.tools:
                    data = await self.tools[action.name](state, **action.params)
                    return AgentResult(success=True, data=data)
                return AgentResult(success=False, error=f"Unknown tool: {action.name}")

            elif action.type == ActionType.ROUTE:
                state.update(current_provider=action.params.get("provider"))
                return AgentResult(success=True, data={"routed_to": action.params.get("provider")})

            elif action.type == ActionType.FALLBACK:
                # Try next provider in chain
                providers = state.available_providers
                current = state.current_provider
                if current in providers:
                    idx = providers.index(current)
                    if idx + 1 < len(providers):
                        next_provider = providers[idx + 1]
                        state.update(current_provider=next_provider)
                        return AgentResult(success=True, data={"fallback_to": next_provider})
                return AgentResult(success=False, error="No more providers in fallback chain")

            elif action.type == ActionType.END:
                state.update(done=True)
                return AgentResult(success=True, data={"completed": True})

            else:
                return AgentResult(success=False, error=f"Unknown action type: {action.type}")

        except Exception as e:
            return AgentResult(success=False, error=str(e))

    def _update_state(self, state: State, action: Action, result: AgentResult):
        """Update state based on action result."""
        if not result.success:
            state.update(error=result.error)
        else:
            state.update(error=None)
            if result.data:
                state.update(result=result.data)
            if result.metadata:
                state.metadata.update(result.metadata)

    def _enforce_constraints(self, state: State) -> bool:
        """Enforce all constraints. Returns True if all constraints satisfied."""
        for constraint in self.constraints:
            try:
                if not constraint(state):
                    return False
            except Exception:
                return False
        return True


# =============================================================================
# Built-in Constraints
# =============================================================================

def max_budget_constraint(budget: float) -> Callable[[State], bool]:
    """Constraint: enforce maximum budget."""
    def constraint(state: State) -> bool:
        spent = state.metadata.get("total_cost", 0)
        return spent <= budget
    return constraint


def max_latency_constraint(max_ms: float) -> Callable[[State], bool]:
    """Constraint: enforce maximum latency."""
    def constraint(state: State) -> bool:
        latency = state.metadata.get("total_latency_ms", 0)
        return latency <= max_ms
    return constraint


def provider_whitelist(allowed: list[str]) -> Callable[[State], bool]:
    """Constraint: only use whitelisted providers."""
    def constraint(state: State) -> bool:
        if state.current_provider:
            return state.current_provider in allowed
        return True
    return constraint
