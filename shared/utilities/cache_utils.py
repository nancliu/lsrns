"""
TTL (Time-To-Live) caching utilities for metadata endpoints.

This module provides caching mechanisms to reduce database load for
frequently accessed metadata that changes infrequently (routes, sections,
demonstrations).
"""

from functools import wraps
from typing import Callable, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)


class TTLCache:
    """
    Simple TTL cache implementation with time-based expiration.

    Attributes:
        maxsize: Maximum number of cached items
        ttl: Time-to-live in seconds (cache validity period)
    """

    def __init__(self, maxsize: int = 100, ttl: int = 300):
        """
        Initialize TTL cache.

        Args:
            maxsize: Maximum cache size (default: 100 items)
            ttl: Cache expiration time in seconds (default: 300s = 5min)
        """
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache = {}
        self._timestamps = {}
        self._hit_count = 0
        self._miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve cached value if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value if valid, None if expired or not found
        """
        if key not in self._cache:
            self._miss_count += 1
            return None

        # Check expiration
        if time.time() - self._timestamps[key] > self.ttl:
            del self._cache[key]
            del self._timestamps[key]
            self._miss_count += 1
            return None

        self._hit_count += 1
        return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache with current timestamp.

        Args:
            key: Cache key
            value: Value to cache
        """
        # Evict oldest item if cache is full
        if len(self._cache) >= self.maxsize and key not in self._cache:
            oldest_key = min(
                self._timestamps.keys(),
                key=lambda k: self._timestamps[k]
            )
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]

        self._cache[key] = value
        self._timestamps[key] = time.time()

    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
        self._timestamps.clear()
        self._hit_count = 0
        self._miss_count = 0

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with hit_count, miss_count, hit_rate, size
        """
        total = self._hit_count + self._miss_count
        hit_rate = (
            self._hit_count / total if total > 0 else 0.0
        )

        return {
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": hit_rate,
            "size": len(self._cache),
            "maxsize": self.maxsize,
            "ttl_seconds": self.ttl
        }


def cached_with_ttl(
    maxsize: int = 100,
    ttl: int = 300
) -> Callable:
    """
    Decorator for caching function results with TTL expiration.

    Args:
        maxsize: Maximum cache size
        ttl: Time-to-live in seconds

    Returns:
        Decorated function with caching

    Example:
        @cached_with_ttl(maxsize=50, ttl=300)
        def get_routes():
            return query_database_for_routes()
    """
    cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(
                    f"Cache HIT for {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "cache_key": cache_key,
                        "cache_stats": cache.get_stats()
                    }
                )
                return cached_value

            # Cache miss - execute function
            logger.debug(
                f"Cache MISS for {func.__name__}",
                extra={
                    "function": func.__name__,
                    "cache_key": cache_key,
                    "cache_stats": cache.get_stats()
                }
            )
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result)

            return result

        # Expose cache for testing/monitoring
        wrapper.cache = cache
        return wrapper

    return decorator
