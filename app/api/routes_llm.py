"""LLM routes - OpenAI Compatible + Streaming."""
import time
import uuid
import json
from fastapi import APIRouter, Depends, Request, Header
from fastapi.responses import StreamingResponse
from typing import Optional

from app.schemas.llm import ChatCompletionRequest, ModelList, ModelInfo
from app.services.llm_router import LLMRouter
from app.services.billing import BillingService
from app.core.security import verify_api_key
from app.db.crud import create_usage_record
from app.db.session import AsyncSessionLocal

router = APIRouter()


@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    request_state: Request,
    api_key_info: dict = Depends(verify_api_key),
):
    """
    OpenAI-compatible Chat Completions endpoint.
    Supports both streaming and non-streaming responses.
    """
    start_time = time.time()
    router_svc = LLMRouter()

    # Build messages format
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    try:
        if request.stream:
            return StreamingResponse(
                stream_response(router_svc, request, api_key_info, start_time),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Request-ID": str(uuid.uuid4()),
                },
            )
        else:
            response = await router_svc.chat_completion(
                model=request.model,
                messages=messages,
                temperature=request.temperature or 1.0,
                max_tokens=request.max_tokens,
            )

            latency_ms = (time.time() - start_time) * 1000
            usage = response.get("usage", {})

            # Log usage to database
            cost = BillingService.calculate_cost(
                model=request.model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
            )

            # Async log to DB
            await log_usage_async(
                api_key_info=api_key_info,
                model=request.model,
                provider=get_provider(request.model),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                cost=cost,
                latency_ms=latency_ms,
                status="success",
            )

            return response

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000

        # Log failed request
        await log_usage_async(
            api_key_info=api_key_info,
            model=request.model,
            provider=get_provider(request.model),
            prompt_tokens=0,
            completion_tokens=0,
            cost=0,
            latency_ms=latency_ms,
            status="error",
        )

        return {
            "error": {
                "message": str(e),
                "type": "internal_error",
                "code": "internal_error",
            }
        }


async def stream_response(
    router_svc: LLMRouter,
    request: ChatCompletionRequest,
    api_key_info: dict,
    start_time: float,
):
    """Stream chat completion response in SSE format."""
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    request_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    first_chunk = True

    try:
        async for chunk in router_svc.chat_completion_stream(
            model=request.model,
            messages=messages,
            temperature=request.temperature or 1.0,
            max_tokens=request.max_tokens,
        ):
            if chunk.startswith("data: "):
                chunk = chunk[6:]

            if chunk == "[DONE]":
                yield "data: [DONE]\n\n"
                break

            # Parse and reformat chunk with proper request_id
            try:
                data = json.loads(chunk)
                if "choices" in data:
                    for choice in data["choices"]:
                        choice["index"] = choice.get("index", 0)
                data["id"] = data.get("id", request_id)
                data["created"] = data.get("created", int(time.time()))
                data["model"] = request.model
                data["object"] = "chat.completion.chunk"

                yield f"data: {json.dumps(data)}\n\n"
                first_chunk = False
            except json.JSONDecodeError:
                yield f"data: {chunk}\n\n"

    except Exception as e:
        error_data = {
            "error": {
                "message": str(e),
                "type": "internal_error",
            }
        }
        yield f"data: {json.dumps(error_data)}\n\n"
    finally:
        # Log completion
        latency_ms = (time.time() - start_time) * 1000
        await log_usage_async(
            api_key_info=api_key_info,
            model=request.model,
            provider=get_provider(request.model),
            prompt_tokens=0,
            completion_tokens=0,
            cost=0,
            latency_ms=latency_ms,
            status="success" if first_chunk else "streamed",
        )


async def log_usage_async(
    api_key_info: dict,
    model: str,
    provider: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost: float,
    latency_ms: float,
    status: str,
):
    """Log usage to database asynchronously."""
    try:
        async with AsyncSessionLocal() as session:
            await create_usage_record(
                db=session,
                tenant_id=api_key_info.get("tenant_id", 1),
                api_key_id=api_key_info.get("api_key_id"),
                model=model,
                provider=provider,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=cost,
                latency_ms=latency_ms,
                status=status,
            )
            await session.commit()
    except Exception as e:
        print(f"Failed to log usage: {e}")


def get_provider(model: str) -> str:
    """Map model to provider name."""
    if model.startswith("gpt") or model.startswith("o1"):
        return "openai"
    elif model.startswith("claude"):
        return "anthropic"
    elif model.startswith("gemini"):
        return "google"
    elif model.startswith("deepseek"):
        return "deepseek"
    elif model.startswith("moonshot"):
        return "moonshot"
    else:
        return "vllm"


# Model registry
MODELS = [
    # OpenAI
    {"id": "gpt-4o", "owned_by": "openai"},
    {"id": "gpt-4o-mini", "owned_by": "openai"},
    {"id": "gpt-4-turbo", "owned_by": "openai"},
    {"id": "gpt-3.5-turbo", "owned_by": "openai"},
    # Anthropic
    {"id": "claude-3-5-sonnet-20240620", "owned_by": "anthropic"},
    {"id": "claude-3-opus", "owned_by": "anthropic"},
    {"id": "claude-3-sonnet", "owned_by": "anthropic"},
    {"id": "claude-3-haiku", "owned_by": "anthropic"},
    # Google
    {"id": "gemini-1.5-pro", "owned_by": "google"},
    {"id": "gemini-1.5-flash", "owned_by": "google"},
    # DeepSeek
    {"id": "deepseek-chat", "owned_by": "deepseek"},
    {"id": "deepseek-coder", "owned_by": "deepseek"},
    # Moonshot
    {"id": "moonshot-v1-8k", "owned_by": "moonshot"},
    {"id": "moonshot-v1-128k", "owned_by": "moonshot"},
    # vLLM (local)
    {"id": "llama-3-70b", "owned_by": "vllm"},
    {"id": "llama-3-8b", "owned_by": "vllm"},
    {"id": "qwen-72b", "owned_by": "vllm"},
]


@router.get("/models", response_model=ModelList)
async def list_models(api_key_info: dict = Depends(verify_api_key)):
    """List available models - OpenAI compatible."""
    return ModelList(
        data=[
            ModelInfo(
                id=m["id"],
                owned_by=m["owned_by"],
                created=1677610602,
            )
            for m in MODELS
        ]
    )


@router.get("/models/{model:path}")
async def get_model(model: str, api_key_info: dict = Depends(verify_api_key)):
    """Get specific model info."""
    for m in MODELS:
        if m["id"] == model:
            return ModelInfo(
                id=m["id"],
                owned_by=m["owned_by"],
                created=1677610602,
            )
    return {"error": {"message": f"Model {model} not found", "type": "invalid_request_error"}}


@router.get("/embeddings")
async def list_embeddings_models(api_key_info: dict = Depends(verify_api_key)):
    """List available embedding models."""
    return {
        "object": "list",
        "data": [
            {"id": "text-embedding-3-small", "object": "model", "created": 1705945660, "owned_by": "openai"},
            {"id": "text-embedding-3-large", "object": "model", "created": 1705945660, "owned_by": "openai"},
            {"id": "text-embedding-ada-002", "object": "model", "created": 1671216899, "owned_by": "openai"},
        ],
    }
