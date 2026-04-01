"""Discord webhook handler for chat completions."""
import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from app.services.discord_service import discord_service
from app.services.llm_router import LLMRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/discord", tags=["discord"])
llm_router = LLMRouter()


class DiscordMessage(BaseModel):
    """Discord webhook message payload."""
    content: Optional[str] = None
    username: Optional[str] = None
    user_id: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat request for Discord."""
    message: str
    model: Optional[str] = "gpt-4o"


class DiscordWebhookPayload(BaseModel):
    """Discord webhook payload from their API."""
    id: Optional[str] = None
    channel_id: Optional[str] = None
    content: Optional[str] = None
    author: Optional[dict] = None
    timestamp: Optional[str] = None


async def process_discord_message(content: str, user_id: str) -> str:
    """Process a Discord message and return LLM response."""
    messages = [{"role": "user", "content": content}]
    response = await llm_router.chat(model="gpt-4o", messages=messages)
    return response


@router.post("/webhook")
async def discord_webhook(
    request: Request,
    x_discord_signature: Optional[str] = Header(None),
    x_discord_timestamp: Optional[str] = Header(None),
):
    """Handle Discord webhook events."""
    body = await request.json()
    logger.info(f"Discord webhook received: {body}")

    payload = DiscordWebhookPayload(**body)
    if not payload.content or not payload.author:
        return {"ok": True}

    username = payload.author.get("username", "unknown")
    user_id = payload.author.get("id", "unknown")

    if payload.content.startswith("/"):
        command = payload.content.split()[0].lower()
        if command == "/help":
            await discord_service.send_message(
                payload.channel_id,
                "**LLM Gateway Commands:**\n"
                "/chat <message> - Chat with AI\n"
                "/models - List available models"
            )
            return {"ok": True}
        elif command == "/models":
            models = llm_router.list_models()
            await discord_service.send_message(
                payload.channel_id,
                "**Available Models:**\n" + "\n".join(f"- {m}" for m in models[:10])
            )
            return {"ok": True}

    try:
        response = await process_discord_message(payload.content, user_id)
        await discord_service.send_message(payload.channel_id, f"**{username}:** {response}")
    except Exception as e:
        logger.error(f"Error processing Discord message: {e}")
        await discord_service.send_message(
            payload.channel_id,
            "Sorry, I encountered an error processing your request."
        )

    return {"ok": True}


@router.get("/status")
async def discord_status():
    """Get Discord bot status."""
    if not discord_service.enabled:
        return {"enabled": False, "message": "Discord not configured"}
    info = await discord_service.get_bot_info()
    return info


class DiscordConfig(BaseModel):
    bot_token: str


@router.post("/configure")
async def configure_discord(config: DiscordConfig):
    """Configure Discord bot."""
    discord_service.configure(config.bot_token)
    verified = await discord_service.verify_bot()
    if not verified:
        discord_service.enabled = False
        raise HTTPException(status_code=400, detail="Invalid Discord bot token")
    return {"ok": True, "message": "Discord configured successfully"}
