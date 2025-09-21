"""Redis caching layer for ReskPoints."""

import asyncio
import json
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta

import aioredis
from aioredis import Redis

from reskpoints.core.config import settings
from reskpoints.core.logging import get_logger

logger = get_logger(__name__)

# Global Redis connection
_redis_client: Optional[Redis] = None


class CacheManager:
    """Redis cache manager with advanced caching strategies."""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.default_ttl = 3600  # 1 hour
        
    async def connect(self):
        """Connect to Redis server."""
        if not settings.REDIS_URL:
            raise ValueError("REDIS_URL not configured")
            
        try:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
            )
            
            # Test connection
            await self.redis.ping()
            logger.info("Connected to Redis cache")
            return self.redis
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Closed Redis connection")
    
    # Basic cache operations
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set value in cache."""
        try:
            serialized_value = json.dumps(value, default=str)
            ttl = ttl or self.default_ttl
            
            if nx:
                result = await self.redis.set(key, serialized_value, ex=ttl, nx=True)
            elif xx:
                result = await self.redis.set(key, serialized_value, ex=ttl, xx=True)
            else:
                result = await self.redis.set(key, serialized_value, ex=ttl)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            result = await self.redis.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            result = await self.redis.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for key."""
        try:
            result = await self.redis.expire(key, ttl)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    # Advanced caching strategies
    async def cache_metrics_summary(
        self,
        provider: str,
        model_name: str,
        summary_data: Dict[str, Any],
        ttl: int = 300,  # 5 minutes
    ):
        """Cache model metrics summary."""
        key = f"metrics:summary:{provider}:{model_name}"
        await self.set(key, summary_data, ttl)
    
    async def get_metrics_summary(
        self,
        provider: str,
        model_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Get cached model metrics summary."""
        key = f"metrics:summary:{provider}:{model_name}"
        return await self.get(key)
    
    async def cache_cost_summary(
        self,
        user_id: Optional[str],
        project_id: Optional[str],
        provider: Optional[str],
        time_range: str,
        summary_data: Dict[str, Any],
        ttl: int = 600,  # 10 minutes
    ):
        """Cache cost summary data."""
        key_parts = ["cost", "summary", time_range]
        if user_id:
            key_parts.append(f"user:{user_id}")
        if project_id:
            key_parts.append(f"project:{project_id}")
        if provider:
            key_parts.append(f"provider:{provider}")
        
        key = ":".join(key_parts)
        await self.set(key, summary_data, ttl)
    
    async def get_cost_summary(
        self,
        user_id: Optional[str],
        project_id: Optional[str],
        provider: Optional[str],
        time_range: str,
    ) -> Optional[Dict[str, Any]]:
        """Get cached cost summary data."""
        key_parts = ["cost", "summary", time_range]
        if user_id:
            key_parts.append(f"user:{user_id}")
        if project_id:
            key_parts.append(f"project:{project_id}")
        if provider:
            key_parts.append(f"provider:{provider}")
        
        key = ":".join(key_parts)
        return await self.get(key)
    
    async def cache_user_quota(
        self,
        user_id: str,
        quota_data: Dict[str, Any],
        ttl: int = 60,  # 1 minute for real-time quota tracking
    ):
        """Cache user quota information."""
        key = f"quota:user:{user_id}"
        await self.set(key, quota_data, ttl)
    
    async def get_user_quota(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user quota information."""
        key = f"quota:user:{user_id}"
        return await self.get(key)
    
    async def increment_usage(
        self,
        user_id: str,
        metric: str,
        amount: int = 1,
        window_seconds: int = 3600,
    ) -> int:
        """Increment usage counter with sliding window."""
        try:
            key = f"usage:{user_id}:{metric}"
            current_time = int(datetime.utcnow().timestamp())
            
            # Use sorted set for sliding window
            await self.redis.zadd(key, {str(current_time): amount})
            
            # Remove old entries outside the window
            cutoff_time = current_time - window_seconds
            await self.redis.zremrangebyscore(key, 0, cutoff_time)
            
            # Set expiration
            await self.redis.expire(key, window_seconds)
            
            # Get current total
            total = await self.redis.zcard(key)
            return total
            
        except Exception as e:
            logger.error(f"Usage increment error for {user_id}:{metric}: {e}")
            return 0
    
    async def get_usage(
        self,
        user_id: str,
        metric: str,
        window_seconds: int = 3600,
    ) -> int:
        """Get current usage count in sliding window."""
        try:
            key = f"usage:{user_id}:{metric}"
            current_time = int(datetime.utcnow().timestamp())
            cutoff_time = current_time - window_seconds
            
            # Count entries in the time window
            count = await self.redis.zcount(key, cutoff_time, current_time)
            return count
            
        except Exception as e:
            logger.error(f"Usage get error for {user_id}:{metric}: {e}")
            return 0
    
    # Cache invalidation patterns
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern."""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.debug(f"Invalidated {len(keys)} keys matching pattern: {pattern}")
        except Exception as e:
            logger.error(f"Pattern invalidation error for {pattern}: {e}")
    
    async def invalidate_user_caches(self, user_id: str):
        """Invalidate all caches for a specific user."""
        patterns = [
            f"cost:*:user:{user_id}*",
            f"quota:user:{user_id}",
            f"usage:{user_id}:*",
        ]
        
        for pattern in patterns:
            await self.invalidate_pattern(pattern)
    
    async def invalidate_provider_caches(self, provider: str):
        """Invalidate all caches for a specific provider."""
        patterns = [
            f"metrics:summary:{provider}:*",
            f"cost:*:provider:{provider}*",
        ]
        
        for pattern in patterns:
            await self.invalidate_pattern(pattern)
    
    # Health and monitoring
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            info = await self.redis.info()
            stats = {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
            }
            
            # Calculate hit rate
            hits = stats["keyspace_hits"]
            misses = stats["keyspace_misses"]
            total = hits + misses
            stats["hit_rate"] = hits / total if total > 0 else 0
            
            return stats
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check cache health."""
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False


# Global cache manager instance
cache_manager = CacheManager()


async def init_cache():
    """Initialize Redis cache connection."""
    global _redis_client
    
    try:
        _redis_client = await cache_manager.connect()
        logger.info("Cache manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize cache: {e}")
        raise


async def close_cache():
    """Close Redis cache connection."""
    await cache_manager.close()


def get_cache() -> CacheManager:
    """Get cache manager instance."""
    if not _redis_client:
        raise RuntimeError("Cache not initialized")
    return cache_manager


# Decorator for caching function results
def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator to cache function results."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cache = get_cache()
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator