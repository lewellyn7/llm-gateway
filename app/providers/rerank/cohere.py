"""Cohere Rerank integration."""

from typing import List, Optional
import httpx
from app.core.config import settings


class CohereRerank:
    """Cohere Rerank API client."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.COHERE_API_KEY
        self.api_url = "https://api.cohere.ai/v1/rerank"

    async def rerank(
        self,
        query: str,
        documents: List[str],
        model: str = "rerank-english-v2.0",
        top_n: Optional[int] = None,
    ) -> dict:
        """
        Rerank documents based on query relevance.

        Args:
            query: The search query
            documents: List of documents to rerank
            model: Rerank model to use
            top_n: Number of top results to return

        Returns:
            Reranked results with scores
        """
        if not self.api_key:
            raise ValueError("Cohere API key is required")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                json={
                    "query": query,
                    "documents": documents,
                    "model": model,
                    "top_n": top_n or len(documents),
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def rerank_with_scores(
        self,
        query: str,
        documents: List[str],
        model: str = "rerank-english-v2.0",
        top_n: Optional[int] = None,
    ) -> List[dict]:
        """Rerank and return results with relevance scores."""
        result = await self.rerank(query, documents, model, top_n)

        results = []
        for item in result.get("results", []):
            results.append(
                {
                    "index": item.get("index"),
                    "document": documents[item.get("index")],
                    "relevance_score": item.get("relevance_score"),
                }
            )

        return results
