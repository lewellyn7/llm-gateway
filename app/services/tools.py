"""
Tool Calling Service - Function calling support
"""
import asyncio
from typing import Any, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum


class ToolCallStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ToolCall:
    """Represents a tool call request."""
    id: str
    name: str
    arguments: dict
    status: ToolCallStatus = ToolCallStatus.PENDING
    result: Any = None
    error: str | None = None


@dataclass
class ToolDefinition:
    """Definition of a callable tool."""
    name: str
    description: str
    parameters: dict  # JSON Schema for parameters
    handler: Callable[..., Awaitable[Any]]


@dataclass
class ToolCallResult:
    """Result of a tool call."""
    tool_call_id: str
    output: Any
    status: ToolCallStatus
    error: str | None = None


class ToolRegistry:
    """Registry for available tools."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        """Register a tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        """List all available tools in OpenAI format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    async def execute(self, name: str, arguments: dict) -> ToolCallResult:
        """Execute a tool by name."""
        tool = self.get(name)
        if not tool:
            return ToolCallResult(
                tool_call_id="",
                output=None,
                status=ToolCallStatus.ERROR,
                error=f"Tool {name} not found",
            )

        try:
            result = await tool.handler(**arguments)
            return ToolCallResult(
                tool_call_id="",
                output=result,
                status=ToolCallStatus.SUCCESS,
            )
        except Exception as e:
            return ToolCallResult(
                tool_call_id="",
                output=None,
                status=ToolCallStatus.ERROR,
                error=str(e),
            )

    async def execute_batch(self, tool_calls: list[ToolCall]) -> list[ToolCallResult]:
        """Execute multiple tool calls concurrently."""
        tasks = [
            self.execute(tc.name, tc.arguments)
            for tc in tool_calls
        ]
        return await asyncio.gather(*tasks)


# Global registry
tool_registry = ToolRegistry()


# =============================================================================
# Built-in Tools
# =============================================================================

async def get_weather(location: str, unit: str = "celsius") -> dict:
    """Get weather for a location."""
    # Placeholder - would call real weather API
    return {
        "location": location,
        "temperature": "22",
        "unit": unit,
        "condition": "sunny",
    }


async def search_web(query: str, limit: int = 5) -> dict:
    """Search the web for information."""
    # Placeholder - would call search API
    return {
        "query": query,
        "results": [
            {"title": f"Result {i}", "url": f"https://example.com/{i}", "snippet": "..."}
            for i in range(limit)
        ],
    }


async def calculate(expression: str) -> dict:
    """Calculate a mathematical expression."""
    try:
        # WARNING: eval can be dangerous, use safe eval in production
        result = eval(expression, {"__builtins__": {}}, {})
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"expression": expression, "error": str(e)}


async def get_current_time(timezone: str = "UTC") -> dict:
    """Get current time for a timezone."""
    from datetime import datetime
    return {
        "timezone": timezone,
        "time": datetime.utcnow().isoformat(),
    }


# Register built-in tools
tool_registry.register(ToolDefinition(
    name="get_weather",
    description="Get current weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius"},
        },
        "required": ["location"],
    },
    handler=get_weather,
))

tool_registry.register(ToolDefinition(
    name="search_web",
    description="Search the web for information",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "limit": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
        },
        "required": ["query"],
    },
    handler=search_web,
))

tool_registry.register(ToolDefinition(
    name="calculate",
    description="Calculate a mathematical expression",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Math expression"},
        },
        "required": ["expression"],
    },
    handler=calculate,
))

tool_registry.register(ToolDefinition(
    name="get_current_time",
    description="Get current time for a timezone",
    parameters={
        "type": "object",
        "properties": {
            "timezone": {"type": "string", "default": "UTC"},
        },
    },
    handler=get_current_time,
))
