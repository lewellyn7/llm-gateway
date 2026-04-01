"""Telegram Bot integration for LLM Gateway."""

import httpx
import asyncio
from typing import Optional, Callable


class TelegramBot:
    """Telegram Bot handler for chat completions."""

    def __init__(self, token: str):
        self.token = token
        self.api_base = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self._running = False
        self._handlers: list[Callable] = []

    async def send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown") -> dict:
        """Send a message to a Telegram chat."""
        url = f"{self.api_base}/sendMessage"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            })
            return response.json()

    async def send_streaming_message(self, chat_id: int, text: str) -> None:
        """Send message with typing indicator for streaming."""
        url = f"{self.api_base}/sendChatAction"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={
                "chat_id": chat_id,
                "action": "typing",
            })

    async def get_updates(self, timeout: int = 30) -> list[dict]:
        """Get updates from Telegram."""
        url = f"{self.api_base}/getUpdates"
        params = {"offset": self.offset, "timeout": timeout}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=params)
            data = response.json()
            if data.get("ok"):
                updates = data.get("result", [])
                if updates:
                    self.offset = updates[-1]["update_id"] + 1
                return updates
            return []

    async def process_updates(self):
        """Process incoming updates."""
        while self._running:
            try:
                updates = await self.get_updates()
                for update in updates:
                    await self._handle_update(update)
            except Exception as e:
                print(f"Error processing updates: {e}")
                await asyncio.sleep(5)

    async def _handle_update(self, update: dict):
        """Handle a single update."""
        message = update.get("message", {})
        if not message:
            return

        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        
        if not chat_id or not text:
            return

        # Call registered handlers
        for handler in self._handlers:
            try:
                await handler(chat_id, text, update)
            except Exception as e:
                print(f"Handler error: {e}")
                await self.send_message(chat_id, f"Error: {str(e)}")

    def register_handler(self, handler: Callable):
        """Register a message handler."""
        self._handlers.append(handler)

    async def set_webhook(self, webhook_url: str) -> dict:
        """Set webhook for Telegram bot."""
        url = f"{self.api_base}/setWebhook"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"url": webhook_url})
            return response.json()

    async def delete_webhook(self) -> dict:
        """Delete webhook."""
        url = f"{self.api_base}/deleteWebhook"
        async with httpx.AsyncClient() as client:
            response = await client.post(url)
            return response.json()

    async def get_me(self) -> dict:
        """Get bot info."""
        url = f"{self.api_base}/getMe"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()

    def start_polling(self):
        """Start polling for updates (run in background)."""
        self._running = True

    def stop_polling(self):
        """Stop polling."""
        self._running = False


class TelegramService:
    """Service for Telegram integration with LLM Gateway."""

    def __init__(self):
        self.bot: Optional[TelegramBot] = None
        self._llm_handler: Optional[Callable] = None

    def init(self, token: str):
        """Initialize Telegram bot."""
        if not token:
            raise ValueError("Telegram bot token is required")
        self.bot = TelegramBot(token)

    async def chat(self, chat_id: int, message: str) -> str:
        """Process chat message and return response."""
        from app.services.llm_router import LLMRouter
        
        router = LLMRouter()
        messages = [{"role": "user", "content": message}]
        
        try:
            response = await router.chat_completion(
                model="gpt-4o-mini",
                messages=messages,
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: {str(e)}"

    async def handle_message(self, chat_id: int, text: str, update: dict):
        """Default message handler."""
        # Show typing indicator
        await self.bot.send_streaming_message(chat_id, "")
        
        # Process and respond
        response = await self.chat(chat_id, text)
        
        # Send response (split if too long)
        if len(response) > 4096:
            for i in range(0, len(response), 4096):
                await self.bot.send_message(chat_id, response[i:i+4096])
        else:
            await self.bot.send_message(chat_id, response)

    def register(self):
        """Register handlers with bot."""
        if self.bot:
            self.bot.register_handler(self.handle_message)

    async def setup_webhook(self, webhook_url: str):
        """Setup webhook mode."""
        if self.bot:
            return await self.bot.set_webhook(webhook_url)
        return {"ok": False, "error": "Bot not initialized"}


# Global instance
telegram_service = TelegramService()
