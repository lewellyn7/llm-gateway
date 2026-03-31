"""Rate limiting with Redis."""
import redis.asyncio as redis
from app.core.config import settings


class RateLimiter:
    """Redis-based sliding window rate limiter."""

    def __init__(self):
        self._client: redis.Redis = None

    async def connect(self):
        self._client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def close(self):
        if self._client:
            await self._client.close()

    async def is_allowed(self, key: str, limit: int = None, window: int = None) -> tuple[bool, int, int]:
        """Check if request is allowed. Returns (allowed, remaining, reset)."""
        limit = limit or settings.RATE_LIMIT_REQUESTS
        window = window or settings.RATE_LIMIT_TTL
        
        now = await self._client.time()
        current_time = int(now[0])
        window_key = f"{key}:window"
        
        await self._client.zremrangebyscore(window_key, 0, current_time - window)
        count = await self._client.zcard(window_key)
        
        if count < limit:
            await self._client.zadd(window_key, {str(current_time): current_time})
            await self._client.expire(window_key, window)
            return True, limit - count - 1, window
        else:
            return False, 0, window


rate_limiter = RateLimiter()
