"""Database caching utilities for improved performance"""

import time
import threading
from typing import Dict, Any, Optional
from collections import OrderedDict


class CacheEntry:
    """Represents a cached item with TTL"""

    def __init__(self, data: Any, ttl_seconds: float):
        self.data = data
        self.expires_at = time.time() + ttl_seconds
        self.created_at = time.time()

    def is_expired(self) -> bool:
        """Check if the cache entry has expired"""
        return time.time() > self.expires_at

    def get_age(self) -> float:
        """Get the age of the cache entry in seconds"""
        return time.time() - self.created_at


class LRUCache:
    """Thread-safe LRU cache with TTL support"""

    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired():
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    self._hits += 1
                    return entry.data
                else:
                    # Remove expired entry
                    del self.cache[key]

            self._misses += 1
            return None

    def put(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Put item in cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]

            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            entry = CacheEntry(value, ttl)

            self.cache[key] = entry
            self.cache.move_to_end(key)

            # Remove oldest items if cache is full
            while len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def invalidate(self, key: str) -> None:
        """Remove item from cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        with self.lock:
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]
            return len(keys_to_remove)

    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests) if total_requests > 0 else 0.0
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'default_ttl': self.default_ttl
            }