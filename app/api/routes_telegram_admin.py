"""Telegram admin API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx

router = APIRouter(prefix="/api/admin/telegram", tags=["admin", "telegram"])


class TelegramSettings(BaseModel):
    enabled: bool = False
    bot_token: Optional[str] = None
    webhook_url: Optional[str] = None
    allowed_chats: List[int] = []


class TelegramStatus(BaseModel):
    configured: bool
    bot_info: Optional[dict] = None
    webhook_set: bool = False


# In-memory settings (in production, store in database)
_telegram_settings = TelegramSettings()


@router.get("/settings")
async def get_telegram_settings():
    """Get current Telegram settings."""
    return _telegram_settings


@router.post("/settings")
async def update_telegram_settings(settings: TelegramSettings):
    """Update Telegram settings."""
    global _telegram_settings

    # Validate bot token if provided
    if settings.bot_token:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.telegram.org/bot{settings.bot_token}/getMe",
                    timeout=10.0,
                )
                if not response.json().get("ok"):
                    raise HTTPException(status_code=400, detail="Invalid bot token")
        except httpx.RequestError:
            raise HTTPException(
                status_code=400, detail="Failed to connect to Telegram API"
            )

    _telegram_settings = settings
    return {"message": "Settings updated", "settings": _telegram_settings}


@router.get("/status")
async def get_telegram_status():
    """Get Telegram connection status."""
    global _telegram_settings

    if not _telegram_settings.bot_token:
        return TelegramStatus(configured=False)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{_telegram_settings.bot_token}/getMe",
                timeout=10.0,
            )
            data = response.json()

            if data.get("ok"):
                return TelegramStatus(
                    configured=True,
                    bot_info={
                        "id": data["result"]["id"],
                        "username": data["result"]["username"],
                        "first_name": data["result"]["first_name"],
                    },
                    webhook_set=_telegram_settings.enabled
                    and bool(_telegram_settings.webhook_url),
                )
            else:
                return TelegramStatus(configured=False)
    except Exception:
        return TelegramStatus(configured=False)


@router.post("/setup-webhook")
async def setup_webhook():
    """Setup Telegram webhook."""
    global _telegram_settings

    if not _telegram_settings.bot_token:
        raise HTTPException(status_code=400, detail="Bot token not configured")

    if not _telegram_settings.webhook_url:
        raise HTTPException(status_code=400, detail="Webhook URL not configured")

    try:
        async with httpx.AsyncClient() as client:
            # Set webhook
            response = await client.post(
                f"https://api.telegram.org/bot{_telegram_settings.bot_token}/setWebhook",
                json={"url": _telegram_settings.webhook_url},
                timeout=10.0,
            )
            result = response.json()

            if result.get("ok"):
                _telegram_settings.enabled = True
                return {"message": "Webhook set successfully", "result": result}
            else:
                raise HTTPException(
                    status_code=500, detail=f"Failed to set webhook: {result}"
                )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to connect to Telegram: {str(e)}"
        )


@router.delete("/webhook")
async def delete_webhook():
    """Delete Telegram webhook."""
    global _telegram_settings

    if not _telegram_settings.bot_token:
        raise HTTPException(status_code=400, detail="Bot token not configured")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{_telegram_settings.bot_token}/deleteWebhook",
                timeout=10.0,
            )
            result = response.json()

            if result.get("ok"):
                _telegram_settings.enabled = False
                return {"message": "Webhook deleted", "result": result}
            else:
                raise HTTPException(
                    status_code=500, detail=f"Failed to delete webhook: {result}"
                )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to connect to Telegram: {str(e)}"
        )


@router.post("/test")
async def test_telegram(chat_id: int, message: str = "Hello from LLM Gateway!"):
    """Send a test message."""
    global _telegram_settings

    if not _telegram_settings.bot_token:
        raise HTTPException(status_code=400, detail="Bot token not configured")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{_telegram_settings.bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": message},
                timeout=10.0,
            )
            result = response.json()

            if result.get("ok"):
                return {"message": "Message sent successfully", "result": result}
            else:
                raise HTTPException(
                    status_code=500, detail=f"Failed to send message: {result}"
                )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to connect to Telegram: {str(e)}"
        )
