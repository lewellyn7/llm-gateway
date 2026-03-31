"""
Models API - OpenAI Compatible
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from app.services.auth import verify_api_key


router = APIRouter()


class Model(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str


class ModelList(BaseModel):
    object: str = "list"
    data: List[Model]


# Available models (would come from database in production)
AVAILABLE_MODELS = [
    {"id": "gpt-4o", "owned_by": "openai"},
    {"id": "gpt-4o-mini", "owned_by": "openai"},
    {"id": "gpt-3.5-turbo", "owned_by": "openai"},
    {"id": "claude-3-5-sonnet", "owned_by": "anthropic"},
    {"id": "claude-3-opus", "owned_by": "anthropic"},
    {"id": "claude-3-haiku", "owned_by": "anthropic"},
    {"id": "vllm-local", "owned_by": "vllm"},
]


@router.get("/models", response_model=ModelList)
async def list_models(api_key_obj: dict = Depends(verify_api_key)):
    """
    List available models.
    OpenAI-compatible endpoint.
    """
    models = [
        Model(
            id=m["id"],
            object="model",
            created=1677610602,  # placeholder
            owned_by=m["owned_by"],
        )
        for m in AVAILABLE_MODELS
    ]
    return ModelList(data=models)
