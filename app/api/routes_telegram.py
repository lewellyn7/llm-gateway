"""Telegram webhook routes."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings
from app.api.channels.telegram import telegram_service

router = APIRouter(prefix="/webhook/telegram", tags=["telegram"])


class TelegramUpdate(BaseModel):
    """Telegram update model."""
    update_id: int
    message: Optional[dict] = None


@router.post(f"/{settings.TELEGRAM_BOT_TOKEN}")
async def telegram_webhook(update: TelegramUpdate, background_tasks: BackgroundTasks):
    """
    Handle Telegram webhook updates.
    
    This endpoint receives updates from Telegram and processes them in background.
    """
    if not update.message:
        return {"ok": True}
    
    chat_id = update.message.get("chat", {}).get("id")
    text = update.message.get("text", "")
    
    if not chat_id or not text:
        return {"ok": True}
    
    # Process in background
    async def process():
        try:
            await telegram_service.handle_message(chat_id, text, update.dict())
        except Exception as e:
            print(f"Telegram handler error: {e}")
    
    background_tasks.add_task(process)
    return {"ok": True}


@router.get("/setup")
async def setup_telegram():
    """Setup Telegram webhook."""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=503, detail="Telegram not configured")
    
    webhook_url = settings.TELEGRAM_WEBHOOK_URL
    if not webhook_url:
        raise HTTPException(status_code=503, detail="Telegram webhook URL not configured")
    
    result = await telegram_service.setup_webhook(webhook_url)
    
    if result.get("ok"):
        return {"message": "Webhook set successfully", "result": result}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to set webhook: {result}")


@router.get("/info")
async def telegram_info():
    """Get Telegram bot info."""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=503, detail="Telegram not configured")
    
    from app.api.channels.telegram import TelegramBot
    bot = TelegramBot(settings.TELEGRAM_BOT_TOKEN)
    return await bot.get_me()


@router.post("/send")
async def send_message(chat_id: int, text: str):
    """Send a message to a Telegram chat (for testing)."""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=503, detail="Telegram not configured")
    
    from app.api.channels.telegram import TelegramBot
    bot = TelegramBot(settings.TELEGRAM_BOT_TOKEN)
    result = await bot.send_message(chat_id, text)
    
    if result.get("ok"):
        return {"message": "Sent successfully"}
    else:
        raise HTTPException(status_code=500, detail=result)
