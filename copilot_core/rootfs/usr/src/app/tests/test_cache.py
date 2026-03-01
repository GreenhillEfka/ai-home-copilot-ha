"""Tests for Cache Manager with LRU Eviction."""

import asyncio
import pytest
import time
from copilot_core.cache import (
    CacheManager,
    CacheConfig,
    CacheMetrics,
    get_sensor_cache,
    get_habitus_cache,
    get_rag_cache,
    init_all_caches,
    shutdown_all_caches,
)


class TestCacheManager:
    """Test cache manager functionality."""
    
    @pytest.fixture
    def cache(self):
        """Create a cache instance for testing."""
        return CacheManager(
            cache_enabled=True,
            default_ttl=300,
            max_size=100,
            cleanup_interval=60,
        )
    
    @pytest.fixture
    def small_cache(self):
        """Create a small cache for LRU testing."""
        return CacheManager(
            cache_enabled=True,
            default_ttl=300,
            max_size=5,  # Very small for testing eviction
            cleanup_interval=60,
        )
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """Test basic set and get operations."""
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache):
        """Test getting a key that doesn't exist."""
        result = await cache.get("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_with_default(self, cache):
        """Test getting a key with default value."""
        result = await cache.get("nonexistent", default="default_value")
        assert result == "default_value"
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        cache = CacheManager(default_ttl=1)  # 1 second TTL
        
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        result = await cache.get("key1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_custom_ttl(self, cache):
        """Test setting custom TTL per key."""
        await cache.set("key1", "value1", ttl=1)  # 1 second
        await cache.set("key2", "value2", ttl=10)  # 10 seconds
        
        # Both should exist
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"
        
        # Wait for first to expire
        await asyncio.sleep(1.1)
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") == "value2"
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self, small_cache):
        """Test LRU eviction when cache exceeds max_size."""
        # Fill cache beyond max_size (5)
        for i in range(7):
            await small_cache.set(f"key{i}", f"value{i}")
        
        # First two keys should be evicted (oldest)
        assert await small_cache.get("key0") is None
        assert await small_cache.get("key1") is None
        
        # Last five should exist
        assert await small_cache.get("key2") == "value2"
        assert await small_cache.get("key3") == "value3"
        assert await small_cache.get("key4") == "value4"
        assert await small_cache.get("key5") == "value5"
        assert await small_cache.get("key6") == "value6"
    
    @pytest.mark.asyncio
    async def test_lru_access_updates_order(self, small_cache):
        """Test that accessing a key moves it to end (most recently used)."""
        # Fill cache
        for i in range(5):
            await small_cache.set(f"key{i}", f"value{i}")
        
        # Access key0 to make it recently used
        await small_cache.get("key0")
        
        # Add new key - should evict key1 (now oldest)
        await small_cache.set("key_new", "value_new")
        
        # key0 should still exist (was accessed recently)
        assert await small_cache.get("key0") == "value0"
        # key1 should be evicted
        assert await small_cache.get("key1") is None
    
    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Test deleting a key."""
        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"
        
        result = await cache.delete("key1")
        assert result is True
        assert await cache.get("key1") is None
        
        # Delete non-existent key
        result = await cache.delete("nonexistent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Test clearing all cache entries."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        await cache.clear()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
    
    @pytest.mark.asyncio
    async def test_exists(self, cache):
        """Test checking if key exists."""
        await cache.set("key1", "value1")
        
        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False
    
    @pytest.mark.asyncio
    async def test_get_or_set(self, cache):
        """Test get_or_set with factory function."""
        call_count = 0
        
        def factory():
            nonlocal call_count
            call_count += 1
            return "computed_value"
        
        # First call - should compute
        result1 = await cache.get_or_set("key1", factory)
        assert result1 == "computed_value"
        assert call_count == 1
        
        # Second call - should use cache
        result2 = await cache.get_or_set("key1", factory)
        assert result2 == "computed_value"
        assert call_count == 1  # Not called again
    
    @pytest.mark.asyncio
    async def test_get_or_set_async_factory(self, cache):
        """Test get_or_set with async factory function."""
        call_count = 0
        
        async def async_factory():
            nonlocal call_count
            call_count += 1
            return "async_value"
        
        result1 = await cache.get_or_set("key1", async_factory)
        assert result1 == "async_value"
        assert call_count == 1
        
        result2 = await cache.get_or_set("key1", async_factory)
        assert result2 == "async_value"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_metrics_tracking(self, cache):
        """Test that cache metrics are tracked correctly."""
        await cache.set("key1", "value1")
        
        # Hit
        await cache.get("key1")
        # Miss
        await cache.get("key2")
        # Another miss
        await cache.get("key3")
        
        metrics = cache.get_metrics()
        assert metrics.hits == 1
        assert metrics.misses == 2
        assert metrics.total_requests == 3
        assert metrics.hit_rate == pytest.approx(1/3, rel=0.01)
    
    @pytest.mark.asyncio
    async def test_stats(self, cache):
        """Test getting cache statistics."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        stats = await cache.get_stats()
        
        assert stats["size"] == 2
        assert stats["max_size"] == 100
        assert stats["enabled"] is True
        assert stats["default_ttl"] == 300
        assert "metrics" in stats
    
    @pytest.mark.asyncio
    async def test_cache_disabled(self):
        """Test that cache can be disabled."""
        cache = CacheManager(cache_enabled=False)
        
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        
        assert result is None  # Cache disabled, so always miss
    
    @pytest.mark.asyncio
    async def test_start_stop(self, cache):
        """Test starting and stopping cache manager."""
        await cache.start()
        assert cache._running is True
        assert cache._cleanup_task is not None
        
        await cache.stop()
        assert cache._running is False
        assert cache._cleanup_task is None


class TestGlobalCaches:
    """Test global cache instances."""
    
    def test_get_sensor_cache(self):
        """Test sensor cache initialization."""
        cache = get_sensor_cache()
        assert cache is not None
        assert cache._config.default_ttl == 300  # 5 minutes
        assert cache._config.max_size == 500
    
    def test_get_habitus_cache(self):
        """Test habitus cache initialization."""
        cache = get_habitus_cache()
        assert cache is not None
        assert cache._config.default_ttl == 900  # 15 minutes
        assert cache._config.max_size == 200
    
    def test_get_rag_cache(self):
        """Test RAG cache initialization."""
        cache = get_rag_cache()
        assert cache is not None
        assert cache._config.default_ttl == 600  # 10 minutes
        assert cache._config.max_size == 1000
    
    @pytest.mark.asyncio
    async def test_init_shutdown_all_caches(self):
        """Test initializing and shutting down all caches."""
        await init_all_caches()
        
        # All caches should be running
        assert get_sensor_cache()._running is True
        assert get_habitus_cache()._running is True
        assert get_rag_cache()._running is True
        
        await shutdown_all_caches()
        
        # All caches should be stopped
        assert get_sensor_cache()._running is False
        assert get_habitus_cache()._running is False
        assert get_rag_cache()._running is False


class TestCacheMetrics:
    """Test cache metrics calculations."""
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        metrics = CacheMetrics(hits=80, misses=20, total_requests=100)
        assert metrics.hit_rate == 0.8
        assert metrics.miss_rate == 0.2
    
    def test_zero_requests(self):
        """Test metrics with zero requests."""
        metrics = CacheMetrics()
        assert metrics.hit_rate == 0.0
        assert metrics.miss_rate == 0.0
    
    def test_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = CacheMetrics(hits=10, misses=5, evictions=2, expirations=3, total_requests=15)
        data = metrics.to_dict()
        
        assert data["hits"] == 10
        assert data["misses"] == 5
        assert data["evictions"] == 2
        assert data["expirations"] == 3
        assert data["total_requests"] == 15
        assert "hit_rate" in data
        assert "miss_rate" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
