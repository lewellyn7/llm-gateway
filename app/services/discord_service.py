"""Discord service for handling bot interactions."""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class DiscordService:
    """Discord bot service."""

    def __init__(self):
        self.bot_token: Optional[str] = None
        self.enabled = False

    def configure(self, bot_token: str):
        """Configure Discord service."""
        self.bot_token = bot_token
        self.enabled = True

    async def verify_bot(self) -> bool:
        """Verify bot token is valid."""
        if not self.bot_token:
            return False
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    "https://discord.com/api/v10/users/@me",
                    headers={"Authorization": f"Bot {self.bot_token}"},
                    timeout=10.0,
                )
                return resp.status_code == 200
            except Exception as e:
                logger.error(f"Discord verify failed: {e}")
                return False

    async def get_bot_info(self) -> dict:
        """Get bot info."""
        if not self.bot_token:
            return {"enabled": False}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    "https://discord.com/api/v10/users/@me",
                    headers={"Authorization": f"Bot {self.bot_token}"},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "enabled": True,
                        "id": data.get("id"),
                        "username": data.get("username"),
                    }
                return {"enabled": False}
            except Exception as e:
                logger.error(f"Discord get info failed: {e}")
                return {"enabled": False}

    async def send_message(self, channel_id: str, content: str) -> bool:
        """Send message to a Discord channel."""
        if not self.bot_token:
            return False
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"https://discord.com/api/v10/channels/{channel_id}/messages",
                    headers={
                        "Authorization": f"Bot {self.bot_token}",
                        "Content-Type": "application/json",
                    },
                    json={"content": content},
                    timeout=30.0,
                )
                return resp.status_code in (200, 201)
            except Exception as e:
                logger.error(f"Discord send message failed: {e}")
                return False

    async def create_webhook(
        self, channel_id: str, name: str = "llm-gateway"
    ) -> Optional[str]:
        """Create webhook in a channel."""
        if not self.bot_token:
            return None
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"https://discord.com/api/v10/channels/{channel_id}/webhooks",
                    headers={
                        "Authorization": f"Bot {self.bot_token}",
                        "Content-Type": "application/json",
                    },
                    json={"name": name},
                    timeout=10.0,
                )
                if resp.status_code in (200, 201):
                    return resp.json().get("token")
                return None
            except Exception as e:
                logger.error(f"Discord create webhook failed: {e}")
                return None


discord_service = DiscordService()
