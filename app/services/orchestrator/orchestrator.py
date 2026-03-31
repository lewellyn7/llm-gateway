"""
Orchestrator - Manages agent execution with state management
"""
from dataclasses import dataclass, field
from typing import Any
import asyncio

from app.services.orchestrator.policy import PolicyEngine, Action, ActionType
from app.services.orchestrator.agent import Agent, AgentContext, AgentResult, get_agent


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
    agent_result: AgentResult | None = None
    metadata: dict = field(default_factory=dict)

    def update(self, **kwargs):
        """Update state fields."""
        for key, value in kwargs.items():
            setattr(self, key, value)


class Orchestrator:
    """
    Orchestrator for managing agent execution.
    
    Execution loop:
    1. Policy decides next action
    2. Execute agent with constraints
    3. Update state with structured result
    4. Enforce constraints
    5. Repeat until done
    """

    def __init__(
        self,
        policy_engine: PolicyEngine | None = None,
        max_iterations: int = 10,
    ):
        self.policy_engine = policy_engine or PolicyEngine(strategy="balanced")
        self.max_iterations = max_iterations
        self.constraints: list = []

    def add_constraint(self, constraint):
        """Add a constraint function. Returns True if satisfied."""
        self.constraints.append(constraint)

    async def run(
        self,
        context: AgentContext,
    ) -> AgentResult:
        """
        Run orchestrator with agent context.
        
        Returns structured AgentResult with result, confidence, cost.
        """
        state = State(
            available_providers=["vllm", "claude", "openai"],
            current_provider=self._get_default_provider(context),
            max_attempts=3,
            metadata={
                "context": context,
            },
        )

        iteration = 0
        
        while not state.done and iteration < self.max_iterations:
            iteration += 1
            state.update(attempt_count=iteration)

            # Policy decides action
            action = self.policy_engine.decide(state.__dict__)

            # Execute
            agent_result = await self._execute_action(action, context, state)

            # Update state
            state.update(agent_result=agent_result)
            if agent_result:
                state.update(result=agent_result.result)
                state.metadata["last_cost"] = agent_result.cost
                
                # Check confidence
                if agent_result.confidence < 0.3:
                    # Low confidence - try fallback
                    state.update(error="Low confidence, trying fallback")
                    continue

                if agent_result.metadata.get("error"):
                    state.update(error=agent_result.metadata["error"])

            # Enforce constraints
            if not self._enforce_constraints(state):
                state.update(done=True, error="Constraint violation")
                return AgentResult(
                    result=None,
                    confidence=0.0,
                    cost=state.metadata.get("total_cost", 0.0),
                    metadata={"error": "Constraint violation"},
                )

            # Check if successful
            if agent_result and agent_result.result and not agent_result.metadata.get("error"):
                state.update(done=True)
                return agent_result

        # Max iterations or done
        total_cost = state.metadata.get("total_cost", 0.0)
        
        if state.error:
            return AgentResult(
                result=None,
                confidence=0.0,
                cost=total_cost,
                metadata={"error": state.error, "iterations": iteration},
            )

        return AgentResult(
            result=state.result,
            confidence=agent_result.confidence if agent_result else 0.0,
            cost=total_cost,
            metadata={"iterations": iteration},
        )

    async def _execute_action(
        self,
        action: Action,
        context: AgentContext,
        state: State,
    ) -> AgentResult | None:
        """Execute a single action."""
        try:
            if action.type == ActionType.AGENT:
                agent = get_agent(action.name)
                if agent:
                    return await agent.run(context)

            elif action.type == ActionType.ROUTE:
                # Update context with routed provider
                provider = action.params.get("provider")
                if provider:
                    state.update(current_provider=provider)
                return AgentResult(
                    result={"routed_to": provider},
                    confidence=1.0,
                    cost=0.0,
                )

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

            elif action.type == ActionType.END:
                state.update(done=True)

        except Exception as e:
            return AgentResult(
                result=None,
                confidence=0.0,
                cost=0.0,
                metadata={"error": str(e)},
            )

        return None

    def _enforce_constraints(self, state: State) -> bool:
        """Enforce all constraints."""
        for constraint in self.constraints:
            try:
                if not constraint(state):
                    return False
            except Exception:
                return False
        return True

    def _get_default_provider(self, context: AgentContext) -> str:
        """Get default provider based on model."""
        model = context.model
        if model.startswith("gpt") or model.startswith("o1"):
            return "openai"
        elif model.startswith("claude"):
            return "claude"
        return "vllm"
