"""
Redis client configuration and dependency injection
"""
import redis
import logging
from typing import Generator, Union
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis connection manager"""
    
    def __init__(self):
        self.client = None
        self.is_mock = False
        try:
            self._initialize()
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using mock Redis client.")
            self.client = MockRedis()
            self.is_mock = True
    
    def _initialize(self):
        """Initialize Redis client (may raise on failure)"""
        # Try to connect to Redis/Memurai
        client = redis.Redis(
            host=getattr(settings, 'redis_host', 'localhost'),
            port=getattr(settings, 'redis_port', 6379),
            db=getattr(settings, 'redis_db', 0),
            password=getattr(settings, 'redis_password', None),
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
        
        # Test connection
        client.ping()
        logger.info("Redis client initialized successfully")
        self.client = client
    
    def get_client(self) -> redis.Redis:
        """Get Redis client"""
        if not self.client:
            self._initialize()
        return self.client


class MockRedis:
    """Mock Redis client for development without Redis"""
    
    def __init__(self):
        self._data = {}
        logger.info("Using MockRedis - no actual Redis connection")
    
    def ping(self):
        """Mock ping"""
        return True
    
    def get(self, key):
        """Mock get"""
        return self._data.get(key)
    
    def set(self, key, value, ex=None):
        """Mock set"""
        self._data[key] = value
        return True
    
    def delete(self, key):
        """Mock delete"""
        if key in self._data:
            del self._data[key]
        return True
    
    def exists(self, key):
        """Mock exists"""
        return key in self._data
    
    def expire(self, key, seconds):
        """Mock expire"""
        return True
    
    def incr(self, key):
        """Mock incr"""
        current = int(self._data.get(key, 0))
        self._data[key] = str(current + 1)
        return current + 1
    
    def setex(self, key, seconds, value):
        """Mock setex"""
        self._data[key] = value
        return True


# Global Redis manager instance
redis_manager = RedisManager()


def get_redis_client() -> Union[redis.Redis, MockRedis]:
    """
    Get Redis client (FastAPI dependency)
    
    Returns:
        Redis client instance (real Redis or MockRedis)
    """
    return redis_manager.get_client()