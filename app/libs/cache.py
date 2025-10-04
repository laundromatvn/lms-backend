"""
Cache implementation for the Laundry Management System.

This module provides caching functionality using Redis for storing
temporary data with TTL (Time To Live) support.
"""

import json
import logging
from typing import Any, List, Optional

import redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Cache manager for handling Redis operations with TTL support.
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis server."""
        try:
            print(settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_PASSWORD)
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                username=settings.REDIS_USERNAME if settings.REDIS_USERNAME else None,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis cache successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """Check if Redis connection is active."""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False
    
    def set(self, key: str, value: Any, ttl_seconds: int = 900) -> bool:
        """
        Set a value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to store (will be JSON serialized)
            ttl_seconds: Time to live in seconds (default: 15 minutes)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            logger.warning("Redis not connected, skipping cache set")
            return False
        
        try:
            # Serialize value to JSON
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)
            
            result = self.redis_client.setex(key, ttl_seconds, serialized_value)
            logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if not self.is_connected():
            logger.warning("Redis not connected, skipping cache get")
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to deserialize JSON, fallback to string
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            logger.warning("Redis not connected, skipping cache delete")
            return False
        
        try:
            result = self.redis_client.delete(key)
            logger.debug(f"Cache delete: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False
    
    def get_ttl(self, key: str) -> int:
        """
        Get the TTL (Time To Live) of a key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, -1 if key doesn't exist, -2 if key has no TTL
        """
        if not self.is_connected():
            return -2
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Failed to get TTL for cache key {key}: {e}")
            return -2
    
    def extend_ttl(self, key: str, ttl_seconds: int) -> bool:
        """
        Extend the TTL of an existing key.
        
        Args:
            key: Cache key
            ttl_seconds: New TTL in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            result = self.redis_client.expire(key, ttl_seconds)
            logger.debug(f"Cache TTL extended: {key} (TTL: {ttl_seconds}s)")
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to extend TTL for cache key {key}: {e}")
            return False
    
    def get_keys(self, pattern: str = "*") -> List[str]:
        """
        Get all keys matching a pattern.
        
        Args:
            pattern: Key pattern (default: all keys)
            
        Returns:
            List of matching keys
        """
        if not self.is_connected():
            return []
        
        try:
            return self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Failed to get keys with pattern {pattern}: {e}")
            return []
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.
        
        Args:
            pattern: Key pattern to clear
            
        Returns:
            Number of keys deleted
        """
        if not self.is_connected():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                result = self.redis_client.delete(*keys)
                logger.info(f"Cleared {result} keys matching pattern: {pattern}")
                return result
            return 0
        except Exception as e:
            logger.error(f"Failed to clear keys with pattern {pattern}: {e}")
            return 0


# Global cache manager instance
cache_manager = CacheManager()


# Convenience functions for global cache manager
def set_cache(key: str, value: Any, ttl_seconds: int = 900) -> bool:
    """Set a value in cache with TTL."""
    return cache_manager.set(key, value, ttl_seconds)


def get_cache(key: str) -> Optional[Any]:
    """Get a value from cache."""
    return cache_manager.get(key)


def delete_cache(key: str) -> bool:
    """Delete a key from cache."""
    return cache_manager.delete(key)


def exists_cache(key: str) -> bool:
    """Check if a key exists in cache."""
    return cache_manager.exists(key)


def get_cache_ttl(key: str) -> int:
    """Get the TTL of a key."""
    return cache_manager.get_ttl(key)


def extend_cache_ttl(key: str, ttl_seconds: int) -> bool:
    """Extend the TTL of a key."""
    return cache_manager.extend_ttl(key, ttl_seconds)
