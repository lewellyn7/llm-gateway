"""
Chat Completions API - OpenAI Compatible
"""
import time
from datetime import datetime
from typing import AsyncIterator, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.auth import verify_api_key
from app.services.router import LLMRouter
from app.services.billing import BillingService


router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[Message]
    stream: bool = False
    temperature: Optional[float] = Field(default=1.0, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=100000)
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1)


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list
    usage: dict


@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None),
    api_key_obj: dict = Depends(verify_api_key),
):
    """
    OpenAI-compatible Chat Completions endpoint.
    """
    # Verify API key
    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid API key")

    tenant_id = api_key_obj.get("tenant_id")
    
    # Route request to appropriate provider
    start_time = time.time()
    router_service = LLMRouter()
    
    try:
        if request.stream:
            return StreamingResponse(
                stream_response(router_service, request, tenant_id),
                media_type="text/event-stream",
            )
        else:
            response = await router_service.route(
                model=request.model,
                messages=[{"role": m.role, "content": m.content} for m in request.messages],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                tenant_id=tenant_id,
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Log usage
            await BillingService.log_usage(
                tenant_id=tenant_id,
                model=request.model,
                prompt_tokens=response.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=response.get("usage", {}).get("completion_tokens", 0),
                latency_ms=latency_ms,
                status="success",
            )
            
            return response
            
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        
        # Log error
        await BillingService.log_usage(
            tenant_id=tenant_id,
            model=request.model,
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=latency_ms,
            status="error",
        )
        
        raise HTTPException(status_code=500, detail=str(e))


async def stream_response(
    router: LLMRouter,
    request: ChatCompletionRequest,
    tenant_id: str,
) -> AsyncIterator[str]:
    """Stream chat completion response."""
    try:
        async for chunk in router.route_stream(
            model=request.model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            tenant_id=tenant_id,
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {str(e)}\n\n"
