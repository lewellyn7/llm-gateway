"""Embeddings routes - OpenAI compatible."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Union, List
from app.core.security import verify_api_key
from app.providers.embeddings import EmbeddingsClient

router = APIRouter()


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str = "text-embedding-3-small"


class EmbeddingData(BaseModel):
    object: str = "embedding"
    embedding: List[float]
    index: int


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: dict


@router.post("/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(
    request: EmbeddingRequest,
    api_key_info: dict = Depends(verify_api_key),
):
    """Create embeddings - OpenAI compatible."""
    client = EmbeddingsClient()

    try:
        response = await client.create(
            input=request.input,
            model=request.model,
        )

        # Convert to our response format
        data = [
            EmbeddingData(
                object="embedding",
                embedding=item["embedding"],
                index=idx,
            )
            for idx, item in enumerate(response.get("data", []))
        ]

        return EmbeddingResponse(
            object="list",
            data=data,
            model=request.model,
            usage=response.get("usage", {}),
        )

    except Exception:
        return EmbeddingResponse(
            object="list",
            data=[],
            model=request.model,
            usage={"prompt_tokens": 0, "total_tokens": 0},
        )
