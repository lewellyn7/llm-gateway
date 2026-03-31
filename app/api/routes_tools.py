"""Tools routes for function calling."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any
from app.core.security import verify_api_key
from app.services.tools import tool_registry

router = APIRouter()


class ToolCall(BaseModel):
    name: str
    arguments: dict


class ToolCallRequest(BaseModel):
    tool_calls: list[ToolCall]


@router.post("/tools/call")
async def call_tool(
    request: ToolCallRequest,
    api_key_info: dict = Depends(verify_api_key),
):
    """Call a registered tool."""
    results = []
    for call in request.tool_calls:
        tool = tool_registry.get(call.name)
        if tool:
            try:
                result = await tool(**call.arguments)
                results.append({"name": call.name, "result": result})
            except Exception as e:
                results.append({"name": call.name, "error": str(e)})
        else:
            results.append({"name": call.name, "error": f"Tool {call.name} not found"})
    return {"results": results}


@router.get("/tools/list")
async def list_tools(api_key_info: dict = Depends(verify_api_key)):
    """List available tools."""
    return {"tools": tool_registry.list_tools()}
