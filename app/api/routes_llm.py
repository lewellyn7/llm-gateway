"""LLM routes - OpenAI compatible."""
import time
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.schemas.llm import ChatCompletionRequest, ModelList, ModelInfo
from app.services.llm_router import LLMRouter
from app.services.billing import BillingService
from app.core.security import verify_api_key

router = APIRouter()


@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    api_key_info: dict = Depends(verify_api_key),
):
    """OpenAI-compatible chat completions."""
    router_svc = LLMRouter()
    start_time = time.time()

    try:
        if request.stream:
            return StreamingResponse(
                stream_response(router_svc, request),
                media_type="text/event-stream",
            )
        else:
            response = await router_svc.chat_completion(
                model=request.model,
                messages=[{"role": m.role, "content": m.content} for m in request.messages],
                temperature=request.temperature or 1.0,
                max_tokens=request.max_tokens,
            )

            latency_ms = (time.time() - start_time) * 1000
            usage = response.get("usage", {})
            
            # Log billing
            cost = BillingService.calculate_cost(
                model=request.model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
            )

            return response

    except Exception as e:
        return {"error": {"message": str(e), "type": "internal_error"}}


async def stream_response(router: LLMRouter, request: ChatCompletionRequest):
    """Stream chat completion response."""
    try:
        async for chunk in router.chat_completion_stream(
            model=request.model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            temperature=request.temperature or 1.0,
            max_tokens=request.max_tokens,
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {str(e)}\n\n"


MODELS = [
    {"id": "gpt-4o", "owned_by": "openai"},
    {"id": "gpt-4o-mini", "owned_by": "openai"},
    {"id": "claude-3-5-sonnet", "owned_by": "anthropic"},
    {"id": "vllm-local", "owned_by": "vllm"},
]


@router.get("/models", response_model=ModelList)
async def list_models(api_key_info: dict = Depends(verify_api_key)):
    """List available models."""
    return ModelList(
        data=[
            ModelInfo(id=m["id"], owned_by=m["owned_by"], created=1677610602)
            for m in MODELS
        ]
    )
