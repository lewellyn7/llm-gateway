"""Tools service for function calling."""
from typing import Any, Callable


class ToolRegistry:
    """Registry for available tools."""

    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        """Register a tool."""
        self._tools[name] = func

    def get(self, name: str) -> Callable | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        """List all available tools."""
        return [
            {"name": name, "description": func.__doc__ or ""}
            for name, func in self._tools.items()
        ]


tool_registry = ToolRegistry()
