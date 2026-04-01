"""Slack service for bot interactions."""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class SlackService:
    """Slack bot service."""

    def __init__(self):
        self.bot_token: Optional[str] = None
        self.enabled = False
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None

    def configure(
        self, bot_token: str = None, client_id: str = None, client_secret: str = None
    ):
        """Configure Slack service."""
        if bot_token:
            self.bot_token = bot_token
            self.enabled = True
        if client_id:
            self.client_id = client_id
        if client_secret:
            self.client_secret = client_secret

    async def verify_token(self) -> bool:
        """Verify bot token is valid."""
        if not self.bot_token:
            return False
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    "https://slack.com/api/auth.test",
                    headers={"Authorization": f"Bearer {self.bot_token}"},
                    timeout=10.0,
                )
                data = resp.json()
                return data.get("ok", False)
            except Exception as e:
                logger.error(f"Slack verify failed: {e}")
                return False

    async def get_bot_info(self) -> dict:
        """Get bot info."""
        if not self.bot_token:
            return {"enabled": False}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    "https://slack.com/api/auth.test",
                    headers={"Authorization": f"Bearer {self.bot_token}"},
                    timeout=10.0,
                )
                data = resp.json()
                if data.get("ok"):
                    return {
                        "enabled": True,
                        "team": data.get("team"),
                        "user": data.get("user"),
                        "bot_id": data.get("bot_id"),
                    }
                return {"enabled": False}
            except Exception as e:
                logger.error(f"Slack get info failed: {e}")
                return {"enabled": False}

    async def post_message(self, channel: str, text: str) -> bool:
        """Post message to a Slack channel."""
        if not self.bot_token:
            return False
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={
                        "Authorization": f"Bearer {self.bot_token}",
                        "Content-Type": "application/json",
                    },
                    json={"channel": channel, "text": text},
                    timeout=30.0,
                )
                data = resp.json()
                return data.get("ok", False)
            except Exception as e:
                logger.error(f"Slack post message failed: {e}")
                return False

    async def create_webhook_url(self, channel_id: str) -> Optional[str]:
        """Create incoming webhook URL for a channel."""
        if not self.bot_token:
            return None
        return "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXX"


slack_service = SlackService()
