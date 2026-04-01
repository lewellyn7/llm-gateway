"""Rerank API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.core.security import verify_api_key
from app.providers.rerank.cohere import CohereRerank

router = APIRouter(prefix="/v1/rerank", tags=["rerank"])


class RerankRequest(BaseModel):
    query: str
    documents: List[str]
    model: str = "rerank-english-v2.0"
    top_n: Optional[int] = None


class RerankResult(BaseModel):
    index: int
    document: str
    relevance_score: float


class RerankResponse(BaseModel):
    id: str
    results: List[RerankResult]
    meta: dict = {}


@router.post("")
async def rerank(
    request: RerankRequest,
    api_key_info: dict = Depends(verify_api_key),
):
    """
    Rerank documents based on query relevance.

    Uses Cohere Rerank API for semantic search refinement.
    """
    try:
        reranker = CohereRerank()
        result = await reranker.rerank(
            query=request.query,
            documents=request.documents,
            model=request.model,
            top_n=request.top_n,
        )

        # Format response
        results = [
            RerankResult(
                index=item["index"],
                document=request.documents[item["index"]],
                relevance_score=item["relevance_score"],
            )
            for item in result.get("results", [])
        ]

        return RerankResponse(
            id=result.get("id", ""),
            results=results,
            meta=result.get("meta", {}),
        )

    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rerank failed: {str(e)}")


@router.post("/simple")
async def rerank_simple(
    query: str,
    documents: List[str],
    top_n: Optional[int] = None,
):
    """
    Simple rerank endpoint without authentication (for testing).
    """
    try:
        reranker = CohereRerank()
        results = await reranker.rerank_with_scores(
            query=query,
            documents=documents,
            top_n=top_n,
        )
        return {"query": query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
