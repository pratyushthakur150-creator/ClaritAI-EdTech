
import time
import json
import logging
from typing import Dict, Optional, Tuple, Any
from enum import Enum
import redis
from redis import Redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class SubscriptionTier(str, Enum):
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"

class RateLimitWindow(str, Enum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"

class RateLimitAlgorithm:
    """Rate limiting algorithms using Redis"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def sliding_window_counter(
        self,
        key: str,
        limit: int,
        window_size: int,
        current_time: Optional[float] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Sliding window counter algorithm using Redis sorted sets
        
        Args:
            key: Redis key for the counter
            limit: Maximum number of requests allowed
            window_size: Window size in seconds
            current_time: Current timestamp (defaults to now)
        
        Returns:
            Tuple of (allowed: bool, info: dict)
        """
        if current_time is None:
            current_time = time.time()
        
        window_start = current_time - window_size
        
        try:
            pipe = self.redis.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, window_size + 60)  # Extra 60 seconds buffer
            
            results = pipe.execute()
            current_count = results[1] + 1  # +1 for the request we just added
            
            if current_count <= limit:
                allowed = True
                remaining = limit - current_count
            else:
                # Remove the request we just added since it's denied
                self.redis.zrem(key, str(current_time))
                allowed = False
                remaining = 0
                current_count -= 1
            
            # Calculate reset time
            oldest_request = self.redis.zrange(key, 0, 0, withscores=True)
            if oldest_request:
                reset_time = oldest_request[0][1] + window_size
            else:
                reset_time = current_time + window_size
            
            return allowed, {
                'limit': limit,
                'remaining': remaining,
                'reset_time': reset_time,
                'current_count': current_count,
                'window_size': window_size
            }
            
        except redis.RedisError as e:
            logger.error(f"Redis error in sliding window counter: {e}")
            # Fail open - allow request if Redis is down
            return True, {
                'limit': limit,
                'remaining': limit - 1,
                'reset_time': current_time + window_size,
                'current_count': 1,
                'window_size': window_size,
                'redis_error': True
            }
    
    async def token_bucket(
        self,
        key: str,
        capacity: int,
        refill_rate: int,
        tokens_requested: int = 1,
        current_time: Optional[float] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Token bucket algorithm using Redis
        
        Args:
            key: Redis key for the bucket
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
            tokens_requested: Tokens needed for this request
            current_time: Current timestamp
        
        Returns:
            Tuple of (allowed: bool, info: dict)
        """
        if current_time is None:
            current_time = time.time()
        
        try:
            # Lua script for atomic token bucket operation
            lua_script = '''
            local key = KEYS[1]
            local capacity = tonumber(ARGV[1])
            local refill_rate = tonumber(ARGV[2])
            local tokens_requested = tonumber(ARGV[3])
            local current_time = tonumber(ARGV[4])
            
            local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
            local tokens = tonumber(bucket[1]) or capacity
            local last_refill = tonumber(bucket[2]) or current_time
            
            -- Calculate tokens to add
            local time_passed = math.max(0, current_time - last_refill)
            local new_tokens = math.min(capacity, tokens + (time_passed * refill_rate))
            
            -- Check if request can be fulfilled
            if new_tokens >= tokens_requested then
                new_tokens = new_tokens - tokens_requested
                redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', current_time)
                redis.call('EXPIRE', key, 3600)  -- 1 hour expiration
                return {1, new_tokens, current_time}
            else
                redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', current_time)
                redis.call('EXPIRE', key, 3600)
                return {0, new_tokens, current_time}
            end
            '''
            
            result = self.redis.eval(
                lua_script, 1, key, 
                capacity, refill_rate, tokens_requested, current_time
            )
            
            allowed = bool(result[0])
            remaining_tokens = result[1]
            
            # Calculate when bucket will have enough tokens
            if not allowed and tokens_requested > 0:
                tokens_needed = tokens_requested - remaining_tokens
                reset_time = current_time + (tokens_needed / refill_rate)
            else:
                reset_time = current_time + ((capacity - remaining_tokens) / refill_rate)
            
            return allowed, {
                'limit': capacity,
                'remaining': int(remaining_tokens),
                'reset_time': reset_time,
                'refill_rate': refill_rate,
                'tokens_requested': tokens_requested
            }
            
        except redis.RedisError as e:
            logger.error(f"Redis error in token bucket: {e}")
            # Fail open
            return True, {
                'limit': capacity,
                'remaining': capacity - tokens_requested,
                'reset_time': current_time + 60,
                'refill_rate': refill_rate,
                'tokens_requested': tokens_requested,
                'redis_error': True
            }

class RateLimitConfig:
    """Rate limiting configuration management"""
    
    # Default rate limits per subscription tier
    DEFAULT_LIMITS = {
        SubscriptionTier.STARTER: {
            RateLimitWindow.MINUTE: 100,
            RateLimitWindow.HOUR: 1000,
            RateLimitWindow.DAY: 10000
        },
        SubscriptionTier.GROWTH: {
            RateLimitWindow.MINUTE: 500,
            RateLimitWindow.HOUR: 10000,
            RateLimitWindow.DAY: 100000
        },
        SubscriptionTier.ENTERPRISE: {
            RateLimitWindow.MINUTE: 2000,
            RateLimitWindow.HOUR: 50000,
            RateLimitWindow.DAY: 1000000
        },
        SubscriptionTier.ADMIN: {
            RateLimitWindow.MINUTE: 10000,
            RateLimitWindow.HOUR: 100000,
            RateLimitWindow.DAY: 10000000
        }
    }
    
    # Window sizes in seconds
    WINDOW_SIZES = {
        RateLimitWindow.MINUTE: 60,
        RateLimitWindow.HOUR: 3600,
        RateLimitWindow.DAY: 86400
    }
    
    # Endpoint-specific multipliers
    ENDPOINT_MULTIPLIERS = {
        '/api/v1/chatbot': 1.0,
        '/api/v1/leads': 0.5,
        '/api/v1/calls': 0.3,
        '/api/v1/demos': 0.2,
        '/api/v1/analytics': 0.1,
        '/api/v1/teaching': 0.5,
        '/api/v1/context': 1.0
    }
    
    @classmethod
    def get_limit(
        self,
        tier: SubscriptionTier,
        window: RateLimitWindow,
        endpoint: Optional[str] = None
    ) -> int:
        """Get rate limit for a specific tier, window, and endpoint"""
        base_limit = self.DEFAULT_LIMITS.get(tier, self.DEFAULT_LIMITS[SubscriptionTier.STARTER])[window]
        
        if endpoint:
            multiplier = self.ENDPOINT_MULTIPLIERS.get(endpoint, 1.0)
            return int(base_limit * multiplier)
        
        return base_limit
    
    @classmethod
    def get_window_size(self, window: RateLimitWindow) -> int:
        """Get window size in seconds"""
        return self.WINDOW_SIZES[window]

class RateLimiter:
    """Main rate limiter class"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.algorithm = RateLimitAlgorithm(redis_client)
        self.config = RateLimitConfig()
    
    def _get_rate_limit_key(
        self,
        tenant_id: str,
        window: RateLimitWindow,
        endpoint: Optional[str] = None
    ) -> str:
        """Generate Redis key for rate limiting"""
        base_key = f"rate_limit:{tenant_id}:{window.value}"
        if endpoint:
            # Clean endpoint for Redis key
            clean_endpoint = endpoint.replace('/', ':').replace('?', '').replace('&', '')
            base_key += f":{clean_endpoint}"
        return base_key
    
    async def check_rate_limit(
        self,
        tenant_id: str,
        tier: SubscriptionTier,
        endpoint: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limits
        
        Returns:
            Tuple of (allowed: bool, limit_info: dict)
        """
        current_time = time.time()
        
        # Check all windows (minute, hour, day)
        for window in [RateLimitWindow.MINUTE, RateLimitWindow.HOUR, RateLimitWindow.DAY]:
            limit = self.config.get_limit(tier, window, endpoint)
            window_size = self.config.get_window_size(window)
            key = self._get_rate_limit_key(tenant_id, window, endpoint)
            
            allowed, info = await self.algorithm.sliding_window_counter(
                key, limit, window_size, current_time
            )
            
            if not allowed:
                info.update({
                    'window': window.value,
                    'tenant_id': tenant_id,
                    'tier': tier.value,
                    'endpoint': endpoint,
                    'user_id': user_id,
                    'ip_address': ip_address,
                    'timestamp': current_time
                })
                return False, info
        
        # If all windows passed, return info from minute window
        minute_limit = self.config.get_limit(tier, RateLimitWindow.MINUTE, endpoint)
        minute_window_size = self.config.get_window_size(RateLimitWindow.MINUTE)
        minute_key = self._get_rate_limit_key(tenant_id, RateLimitWindow.MINUTE, endpoint)
        
        _, minute_info = await self.algorithm.sliding_window_counter(
            minute_key, minute_limit, minute_window_size, current_time
        )
        
        minute_info.update({
            'window': RateLimitWindow.MINUTE.value,
            'tenant_id': tenant_id,
            'tier': tier.value,
            'endpoint': endpoint,
            'user_id': user_id,
            'ip_address': ip_address,
            'timestamp': current_time
        })
        
        return True, minute_info
    
    async def get_rate_limit_status(
        self,
        tenant_id: str,
        tier: SubscriptionTier,
        endpoint: str
    ) -> Dict[str, Dict[str, Any]]:
        """Get current rate limit status for all windows"""
        status = {}
        current_time = time.time()
        
        for window in [RateLimitWindow.MINUTE, RateLimitWindow.HOUR, RateLimitWindow.DAY]:
            limit = self.config.get_limit(tier, window, endpoint)
            window_size = self.config.get_window_size(window)
            key = self._get_rate_limit_key(tenant_id, window, endpoint)
            
            try:
                current_count = self.redis.zcount(
                    key, current_time - window_size, current_time
                )
                remaining = max(0, limit - current_count)
                
                # Get oldest request for reset time
                oldest_request = self.redis.zrange(key, 0, 0, withscores=True)
                if oldest_request:
                    reset_time = oldest_request[0][1] + window_size
                else:
                    reset_time = current_time + window_size
                
                status[window.value] = {
                    'limit': limit,
                    'remaining': remaining,
                    'current_count': current_count,
                    'reset_time': reset_time,
                    'window_size': window_size
                }
                
            except redis.RedisError as e:
                logger.error(f"Redis error getting status for {key}: {e}")
                status[window.value] = {
                    'limit': limit,
                    'remaining': limit,
                    'current_count': 0,
                    'reset_time': current_time + window_size,
                    'window_size': window_size,
                    'redis_error': True
                }
        
        return status
