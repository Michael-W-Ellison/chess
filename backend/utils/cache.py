"""
Response Caching Utilities
Provides caching mechanisms for expensive operations like LLM generation
"""

import hashlib
import json
import logging
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
from collections import OrderedDict

logger = logging.getLogger("chatbot.cache")


class TTLCache:
    """
    Time-To-Live Cache - stores items with expiration times
    Thread-safe cache with automatic cleanup of expired entries
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        Initialize TTL cache

        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
            max_size: Maximum number of items to cache (default: 1000)
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]

        # Check if expired
        if time.time() > entry['expires_at']:
            # Remove expired entry
            del self._cache[key]
            self._misses += 1
            logger.debug(f"Cache MISS (expired): {key[:50]}...")
            return None

        # Move to end (LRU)
        self._cache.move_to_end(key)
        self._hits += 1
        logger.debug(f"Cache HIT: {key[:50]}...")
        return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache with TTL

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl

        # Evict oldest if at max size
        if len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Cache eviction (max size): {oldest_key[:50]}...")

        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time(),
        }
        logger.debug(f"Cache SET: {key[:50]}... (TTL: {ttl}s)")

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache DELETE: {key[:50]}...")
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("Cache cleared")

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries

        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry['expires_at']
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'total_requests': total_requests,
        }


class LRUCache:
    """
    Least Recently Used Cache - evicts least recently used items when full
    Simpler than TTL cache, no expiration
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize LRU cache

        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """Get value and move to end (most recent)"""
        if key not in self._cache:
            return None

        self._cache.move_to_end(key)
        return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        """Set value, evicting oldest if necessary"""
        if key in self._cache:
            self._cache.move_to_end(key)
        elif len(self._cache) >= self.max_size:
            # Evict oldest
            self._cache.popitem(last=False)

        self._cache[key] = value

    def clear(self) -> None:
        """Clear all entries"""
        self._cache.clear()


def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from function arguments

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Hash string for use as cache key
    """
    # Create stable representation of arguments
    key_dict = {
        'args': args,
        'kwargs': sorted(kwargs.items()),
    }

    # Convert to JSON and hash
    key_str = json.dumps(key_dict, sort_keys=True, default=str)
    return hashlib.sha256(key_str.encode()).hexdigest()


def cached(ttl: int = 300, cache_instance: Optional[TTLCache] = None):
    """
    Decorator for caching function results with TTL

    Args:
        ttl: Time-to-live in seconds
        cache_instance: Specific cache instance to use (creates default if None)

    Returns:
        Decorated function with caching
    """
    if cache_instance is None:
        cache_instance = TTLCache(default_ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{generate_cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result, ttl=ttl)

            return result

        # Expose cache for manual control
        wrapper._cache = cache_instance
        wrapper._cache_key = lambda *args, **kwargs: f"{func.__name__}:{generate_cache_key(*args, **kwargs)}"

        return wrapper

    return decorator


# Global cache instances for different use cases
llm_response_cache = TTLCache(default_ttl=3600, max_size=500)  # 1 hour, 500 responses
personality_cache = TTLCache(default_ttl=60, max_size=100)     # 1 minute, 100 personalities
profile_cache = TTLCache(default_ttl=300, max_size=100)        # 5 minutes, 100 profiles
template_cache = LRUCache(max_size=1000)                       # No expiration, 1000 templates
