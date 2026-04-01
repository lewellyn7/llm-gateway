"""Slack webhook handler for chat completions."""
import logging
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.slack_service import slack_service
from app.services.llm_router import LLMRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/slack", tags=["slack"])
llm_router = LLMRouter()


class SlackMessage(BaseModel):
    """Slack message payload."""
    type: str
    channel: str
    user: str
    text: Optional[str] = None
    command: Optional[str] = None


class SlackWebhookPayload(BaseModel):
    """Slack webhook payload."""
    type: Optional[str] = None
    challenge: Optional[str] = None
    token: Optional[str] = None
    team_id: Optional[str] = None
    event: Optional[dict] = None


async def process_slack_message(text: str, user: str, channel: str) -> str:
    """Process a Slack message and return LLM response."""
    messages = [{"role": "user", "content": text}]
    response = await llm_router.chat(model="gpt-4o", messages=messages)
    return response


@router.post("/webhook")
async def slack_webhook(request: Request):
    """Handle Slack webhook events."""
    body = await request.json()
    logger.info(f"Slack webhook received: {body}")

    if body.get("type") == "url_verification":
        return {"challenge": body.get("challenge")}

    event = body.get("event", {})
    if not event:
        return {"ok": True}

    event_type = event.get("type")
    if event_type == "app_mention":
        user = event.get("user")
        channel = event.get("channel")
        text = event.get("text", "")

        text = text.replace("<@U00000000>", "").strip()

        if text.startswith("/help"):
            await slack_service.post_message(
                channel,
                "*LLM Gateway Commands:*\n"
                "/chat <message> - Chat with AI\n"
                "/models - List available models"
            )
            return {"ok": True}
        elif text.startswith("/models"):
            models = llm_router.list_models()
            await slack_service.post_message(
                channel,
                "*Available Models:*\n" + "\n".join(f"• {m}" for m in models[:10])
            )
            return {"ok": True}

        try:
            response = await process_slack_message(text, user, channel)
            await slack_service.post_message(channel, f"<@{user}> {response}")
        except Exception as e:
            logger.error(f"Error processing Slack message: {e}")
            await slack_service.post_message(channel, "Sorry, I encountered an error.")

        return {"ok": True}

    if event_type == "message" and not event.get("subtype"):
        user = event.get("user")
        channel = event.get("channel")
        text = event.get("text", "")

        if "hello" in text.lower() or "hi" in text.lower():
            await slack_service.post_message(channel, f"Hi <@{user}>! Use @llm-gateway to chat with me.")
            return {"ok": True}

    return {"ok": True}


@router.get("/status")
async def slack_status():
    """Get Slack bot status."""
    if not slack_service.enabled:
        return {"enabled": False, "message": "Slack not configured"}
    info = await slack_service.get_bot_info()
    return info


class SlackConfig(BaseModel):
    bot_token: str


@router.post("/configure")
async def configure_slack(config: SlackConfig):
    """Configure Slack bot."""
    slack_service.configure(bot_token=config.bot_token)
    verified = await slack_service.verify_token()
    if not verified:
        slack_service.enabled = False
        return {"ok": False, "message": "Invalid Slack bot token"}
    return {"ok": True, "message": "Slack configured successfully"}
