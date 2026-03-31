"""
Redis Connection for Rate Limiting and Caching
"""
import redis.asyncio as redis
from app.core.config import settings


class RedisClient:
    """Async Redis client."""

    def __init__(self):
        self._client: redis.Redis = None

    async def connect(self):
        """Connect to Redis."""
        self._client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()

    async def get(self, key: str) -> str | None:
        """Get a value."""
        return await self._client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
    ) -> bool:
        """Set a value with optional expiration."""
        return await self._client.set(key, value, ex=ex)

    async def incr(self, key: str) -> int:
        """Increment a key."""
        return await self._client.incr(key)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key."""
        return await self._client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """Get TTL of a key."""
        return await self._client.ttl(key)

    async def sliding_window_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> tuple[bool, int, int]:
        """
        Sliding window rate limiting.
        Returns: (allowed, remaining, reset_time)
        """
        now = await self._client.time()
        current_time = int(now[0])

        # Remove old entries outside the window
        window_key = f"{key}:window"
        await self._client.zremrangebyscore(window_key, 0, current_time - window)

        # Count requests in current window
        count = await self._client.zcard(window_key)

        if count < limit:
            # Add current request
            await self._client.zadd(window_key, {str(current_time): current_time})
            await self._client.expire(window_key, window)
            return True, limit - count - 1, window
        else:
            # Get oldest entry to calculate reset time
            oldest = await self._client.zrange(window_key, 0, 0, withscores=True)
            reset_time = int(oldest[0][1]) + window if oldest else current_time + window
            return False, 0, reset_time


redis_client = RedisClient()
