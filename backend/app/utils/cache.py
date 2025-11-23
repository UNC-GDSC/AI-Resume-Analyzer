"""Redis caching service."""

import json
from typing import Any, Optional
import redis
from app.core.config import settings
from loguru import logger


class CacheService:
    """Redis cache service."""

    def __init__(self):
        """Initialize cache service."""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis not available: {str(e)}")
            self.redis_client = None

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.redis_client:
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None

    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds

        Returns:
            True if successful
        """
        if not self.redis_client:
            return False

        try:
            self.redis_client.setex(
                key,
                expire,
                json.dumps(value)
            )
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        if not self.redis_client:
            return False

        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False

    def clear_pattern(self, pattern: str) -> bool:
        """Clear all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "job:*")

        Returns:
            True if successful
        """
        if not self.redis_client:
            return False

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Cache clear pattern error: {str(e)}")
            return False


# Global cache instance
cache = CacheService()
