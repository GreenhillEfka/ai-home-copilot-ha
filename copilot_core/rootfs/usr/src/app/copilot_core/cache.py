"""In-Memory Cache Manager with LRU Eviction.

Features:
- Async-safe with asyncio.Lock
- TTL-based expiration
- LRU eviction on memory pressure
- Cache hit/miss metrics
- Configurable: cache_enabled, default_ttl, max_size
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Generic, TypeVar

_LOGGER = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with value, timestamp, and access tracking."""
    
    value: T
    created_at: float
    expires_at: float
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    total_requests: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate (0.0 to 1.0)."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate (0.0 to 1.0)."""
        if self.total_requests == 0:
            return 0.0
        return self.misses / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "total_requests": self.total_requests,
            "hit_rate": round(self.hit_rate, 4),
            "miss_rate": round(self.miss_rate, 4),
        }


@dataclass
class CacheConfig:
    """Configuration for cache manager."""
    
    cache_enabled: bool = True
    default_ttl: int = 300  # 5 minutes
    max_size: int = 1000
    cleanup_interval: int = 60  # seconds


class CacheManager:
    """Thread-safe in-memory cache with LRU eviction.
    
    Features:
    - asyncio.Lock for async safety
    - TTL-based automatic expiration
    - LRU eviction when max_size is reached
    - Per-key TTL override
    - Hit/miss metrics tracking
    - Background cleanup task
    
    Usage:
        cache = CacheManager(max_size=1000, default_ttl=300)
        await cache.set("key", value, ttl=600)
        value = await cache.get("key")
        await cache.delete("key")
    """
    
    def __init__(
        self,
        cache_enabled: bool = True,
        default_ttl: int = 300,
        max_size: int = 1000,
        cleanup_interval: int = 60,
    ):
        self._cache: OrderedDict[str, CacheEntry[Any]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._metrics = CacheMetrics()
        self._config = CacheConfig(
            cache_enabled=cache_enabled,
            default_ttl=default_ttl,
            max_size=max_size,
            cleanup_interval=cleanup_interval,
        )
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        _LOGGER.info(
            "CacheManager initialized: enabled=%s, max_size=%d, default_ttl=%ds",
            cache_enabled, max_size, default_ttl
        )
    
    async def start(self) -> None:
        """Start background cleanup task."""
        if self._config.cache_enabled and not self._running:
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            _LOGGER.info("CacheManager cleanup task started")
    
    async def stop(self) -> None:
        """Stop background cleanup task."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            _LOGGER.info("CacheManager cleanup task stopped")
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired entries."""
        while self._running:
            try:
                await asyncio.sleep(self._config.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                _LOGGER.error("Cache cleanup error: %s", e)
    
    async def _cleanup_expired(self) -> int:
        """Remove expired entries. Returns count of removed entries."""
        now = time.time()
        expired_keys = []
        
        async with self._lock:
            for key, entry in self._cache.items():
                if now > entry.expires_at:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self._metrics.expirations += 1
        
        if expired_keys:
            _LOGGER.debug("Cleaned up %d expired cache entries", len(expired_keys))
        
        return len(expired_keys)
    
    async def _evict_if_needed(self) -> None:
        """Evict oldest entries if cache exceeds max_size."""
        # Evict until we have room for one more item
        while len(self._cache) >= self._config.max_size:
            # Remove oldest (first) item - LRU eviction
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._metrics.evictions += 1
            _LOGGER.debug("Evicted cache entry: %s", oldest_key)
    
    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found or expired
            
        Returns:
            Cached value or default
        """
        if not self._config.cache_enabled:
            self._metrics.misses += 1
            self._metrics.total_requests += 1
            return default
        
        now = time.time()
        
        async with self._lock:
            if key not in self._cache:
                self._metrics.misses += 1
                self._metrics.total_requests += 1
                return default
            
            entry = self._cache[key]
            
            # Check expiration
            if now > entry.expires_at:
                del self._cache[key]
                self._metrics.expirations += 1
                self._metrics.misses += 1
                self._metrics.total_requests += 1
                return default
            
            # Update access tracking (move to end for LRU)
            entry.last_accessed = now
            entry.access_count += 1
            self._cache.move_to_end(key)
            
            self._metrics.hits += 1
            self._metrics.total_requests += 1
            
            _LOGGER.debug("Cache hit: %s (access_count=%d)", key, entry.access_count)
            return entry.value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (overrides default_ttl)
        """
        if not self._config.cache_enabled:
            return
        
        now = time.time()
        effective_ttl = ttl if ttl is not None else self._config.default_ttl
        expires_at = now + effective_ttl
        
        async with self._lock:
            # If key exists, remove it first (will re-add at end)
            if key in self._cache:
                del self._cache[key]
            
            # Evict if needed before adding
            await self._evict_if_needed()
            
            entry = CacheEntry(
                value=value,
                created_at=now,
                expires_at=expires_at,
                last_accessed=now,
                access_count=0,
            )
            self._cache[key] = entry
            
            _LOGGER.debug("Cache set: %s (ttl=%ds)", key, effective_ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache.
        
        Returns:
            True if key was deleted, False if not found
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                _LOGGER.debug("Cache delete: %s", key)
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            _LOGGER.info("Cache cleared")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        if not self._config.cache_enabled:
            return False
        
        now = time.time()
        
        async with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            if now > entry.expires_at:
                del self._cache[key]
                self._metrics.expirations += 1
                return False
            
            return True
    
    async def get_or_set(
        self,
        key: str,
        factory: Any,
        ttl: Optional[int] = None,
    ) -> Any:
        """Get value from cache or compute and cache it.
        
        Args:
            key: Cache key
            factory: Async callable to compute value if not cached
            ttl: Time-to-live in seconds
            
        Returns:
            Cached or computed value
        """
        value = await self.get(key)
        if value is not None:
            return value
        
        # Compute value
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()
        
        # Cache it
        await self.set(key, value, ttl=ttl)
        return value
    
    def get_metrics(self) -> CacheMetrics:
        """Get cache metrics."""
        return self._metrics
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            now = time.time()
            expired_count = sum(
                1 for entry in self._cache.values()
                if now > entry.expires_at
            )
            
            return {
                "size": len(self._cache),
                "max_size": self._config.max_size,
                "enabled": self._config.cache_enabled,
                "default_ttl": self._config.default_ttl,
                "expired_entries": expired_count,
                "metrics": self._metrics.to_dict(),
            }


# Global cache instances for different use cases
_sensor_cache: Optional[CacheManager] = None
_habitus_cache: Optional[CacheManager] = None
_rag_cache: Optional[CacheManager] = None


def get_sensor_cache() -> CacheManager:
    """Get or create sensor cache (5 min TTL)."""
    global _sensor_cache
    if _sensor_cache is None:
        _sensor_cache = CacheManager(
            cache_enabled=True,
            default_ttl=300,  # 5 minutes
            max_size=500,
            cleanup_interval=30,
        )
    return _sensor_cache


def get_habitus_cache() -> CacheManager:
    """Get or create habitus cache (15 min TTL)."""
    global _habitus_cache
    if _habitus_cache is None:
        _habitus_cache = CacheManager(
            cache_enabled=True,
            default_ttl=900,  # 15 minutes
            max_size=200,
            cleanup_interval=60,
        )
    return _habitus_cache


def get_rag_cache() -> CacheManager:
    """Get or create RAG cache (10 min TTL)."""
    global _rag_cache
    if _rag_cache is None:
        _rag_cache = CacheManager(
            cache_enabled=True,
            default_ttl=600,  # 10 minutes
            max_size=1000,
            cleanup_interval=45,
        )
    return _rag_cache


def get_rag_bm25_cache() -> CacheManager:
    """Alias for get_rag_cache() - for BM25 search result caching."""
    return get_rag_cache()


async def init_all_caches() -> None:
    """Initialize and start all cache managers."""
    for cache in [get_sensor_cache(), get_habitus_cache(), get_rag_cache()]:
        await cache.start()


async def shutdown_all_caches() -> None:
    """Stop all cache managers."""
    for cache in [get_sensor_cache(), get_habitus_cache(), get_rag_cache()]:
        await cache.stop()
