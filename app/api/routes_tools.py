"""Tools routes for function calling."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Any, List

from app.core.security import verify_api_key
from app.services.tools import tool_registry

router = APIRouter()


# =============================================================================
# Schemas
# =============================================================================

class FunctionCall(BaseModel):
    """A single function call."""
    name: str
    arguments: dict = Field(default_factory=dict)


class ToolCallRequest(BaseModel):
    """Request to call tools."""
    tool_calls: List[FunctionCall]


class ToolCallResult(BaseModel):
    """Result of a single tool call."""
    name: str
    output: Any = None
    error: str | None = None


class ToolListItem(BaseModel):
    """A tool in the list."""
    type: str = "function"
    function: dict


class ToolListResponse(BaseModel):
    """Response listing available tools."""
    tools: List[ToolListItem]


# =============================================================================
# Routes
# =============================================================================

@router.post("/tools/call", response_model=dict)
async def call_tools(
    request: ToolCallRequest,
    api_key_info: dict = Depends(verify_api_key),
):
    """
    Call one or more tools.
    
    Example:
    {
        "tool_calls": [
            {"name": "get_weather", "arguments": {"location": "Beijing"}},
            {"name": "calculate", "arguments": {"expression": "2+2"}}
        ]
    }
    """
    results = []

    for call in request.tool_calls:
        tool = tool_registry.get(call.name)
        if not tool:
            results.append(ToolCallResult(
                name=call.name,
                output=None,
                error=f"Tool {call.name} not found",
            ))
            continue

        try:
            output = await tool.handler(**call.arguments)
            results.append(ToolCallResult(
                name=call.name,
                output=output,
            ))
        except Exception as e:
            results.append(ToolCallResult(
                name=call.name,
                output=None,
                error=str(e),
            ))

    return {
        "results": [
            {
                "name": r.name,
                "output": r.output,
                "error": r.error,
            }
            for r in results
        ]
    }


@router.get("/tools/list", response_model=ToolListResponse)
async def list_tools(
    api_key_info: dict = Depends(verify_api_key),
):
    """List all available tools."""
    return ToolListResponse(
        tools=[
            ToolListItem(
                type="function",
                function={
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            )
            for t in tool_registry._tools.values()
        ]
    )


@router.post("/tools/parallel")
async def call_tools_parallel(
    request: ToolCallRequest,
    api_key_info: dict = Depends(verify_api_key),
):
    """Call multiple tools in parallel for better performance."""
    import asyncio

    async def call_one(call: FunctionCall):
        tool = tool_registry.get(call.name)
        if not tool:
            return {"name": call.name, "output": None, "error": f"Tool {call.name} not found"}
        try:
            output = await tool.handler(**call.arguments)
            return {"name": call.name, "output": output}
        except Exception as e:
            return {"name": call.name, "output": None, "error": str(e)}

    results = await asyncio.gather(*[call_one(c) for c in request.tool_calls])

    return {"results": list(results)}
