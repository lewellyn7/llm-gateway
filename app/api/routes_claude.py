"""Claude-specific routes."""

from fastapi import APIRouter, Depends
from app.core.security import verify_api_key

router = APIRouter()


@router.get("/claude/status")
async def claude_status(api_key_info: dict = Depends(verify_api_key)):
    """Check Claude API status."""
    return {"status": "operational", "provider": "anthropic"}
