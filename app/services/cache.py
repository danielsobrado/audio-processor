"""
Redis caching service.
"""

import logging
from typing import Any

import redis.asyncio as redis

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheService:
    """
    Service for interacting with Redis cache.
    """

    def __init__(self):
        self.redis_client = redis.from_url(settings.redis.url)

    async def get(self, key: str) -> Any | None:
        """
        Get a value from the cache.

        Args:
            key: The key to retrieve.

        Returns:
            The value from the cache, or None if not found or on error.
        """

        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Failed to get key {key} from cache: {e}", exc_info=True)
            return None

    async def set(self, key: str, value: Any, expire: int = 3600) -> None:
        """
        Set a value in the cache.

        Args:
            key: The key to set.
            value: The value to set.
            expire: The expiration time in seconds.
        """

        try:
            await self.redis_client.set(key, value, ex=expire)
        except Exception as e:
            logger.error(f"Failed to set key {key} in cache: {e}", exc_info=True)

    async def delete(self, key: str) -> None:
        """
        Delete a key from the cache.

        Args:
            key: The key to delete.
        """

        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Failed to delete key {key} from cache: {e}", exc_info=True)
