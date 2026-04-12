#!/usr/bin/env python3
"""
Rate Limiting Examples for Ravian Backend API

This file demonstrates how to use the rate limiting system
with different subscription tiers and endpoints.
"""

import asyncio
import time
import redis
from app.core.rate_limiter import RateLimiter, SubscriptionTier, RateLimitConfig

async def example_rate_limiting():
    """Example usage of the rate limiting system"""
    
    # Initialize Redis client
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True
    )
    
    # Test Redis connection
    try:
        redis_client.ping()
        print("✓ Redis connection successful")
    except redis.RedisError as e:
        print(f"✗ Redis connection failed: {e}")
        return
    
    # Create rate limiter
    rate_limiter = RateLimiter(redis_client)
    
    # Example 1: Check rate limits for different tiers
    print("\n=== Rate Limiting Examples ===\n")
    
    tenants = [
        ("tenant-starter-123", SubscriptionTier.STARTER),
        ("tenant-growth-456", SubscriptionTier.GROWTH),
        ("tenant-enterprise-789", SubscriptionTier.ENTERPRISE)
    ]
    
    endpoints = [
        "/api/v1/chatbot",
        "/api/v1/leads", 
        "/api/v1/analytics"
    ]
    
    for tenant_id, tier in tenants:
        print(f"\nTenant: {tenant_id} (Tier: {tier.value})")
        print("-" * 50)
        
        for endpoint in endpoints:
            # Check rate limit status
            allowed, info = await rate_limiter.check_rate_limit(
                tenant_id=tenant_id,
                tier=tier,
                endpoint=endpoint,
                user_id=f"user-{tenant_id}"
            )
            
            print(f"Endpoint: {endpoint}")
            print(f"  Allowed: {allowed}")
            print(f"  Limit: {info['limit']}")
            print(f"  Remaining: {info['remaining']}")
            print(f"  Window: {info['window']}")
            print(f"  Reset Time: {time.ctime(info['reset_time'])}")
            
            # Make a few more requests to see rate limiting in action
            for i in range(3):
                allowed, info = await rate_limiter.check_rate_limit(
                    tenant_id=tenant_id,
                    tier=tier,
                    endpoint=endpoint
                )
                print(f"  Request {i+2}: Allowed={allowed}, Remaining={info['remaining']}")
    
    # Example 2: Demonstrate rate limit status for all windows
    print("\n=== Rate Limit Status (All Windows) ===\n")
    
    tenant_id = "test-tenant"
    tier = SubscriptionTier.STARTER
    endpoint = "/api/v1/chatbot"
    
    status = await rate_limiter.get_rate_limit_status(tenant_id, tier, endpoint)
    
    print(f"Rate Limit Status for {tenant_id}:")
    for window, info in status.items():
        print(f"  {window.upper()}:")
        print(f"    Limit: {info['limit']}")
        print(f"    Remaining: {info['remaining']}")
        print(f"    Current Count: {info['current_count']}")
        print(f"    Reset Time: {time.ctime(info['reset_time'])}")
    
    # Example 3: Test rate limiting with rapid requests
    print("\n=== Rapid Requests Test ===\n")
    
    tenant_id = "rapid-test-tenant"
    tier = SubscriptionTier.STARTER
    endpoint = "/api/v1/chatbot"
    
    print(f"Making 10 rapid requests for {tenant_id}...")
    
    for i in range(10):
        allowed, info = await rate_limiter.check_rate_limit(
            tenant_id=tenant_id,
            tier=tier,
            endpoint=endpoint
        )
        
        status = "✓ ALLOWED" if allowed else "✗ BLOCKED"
        print(f"Request {i+1:2d}: {status} (Remaining: {info['remaining']}, Limit: {info['limit']})")
        
        if not allowed:
            retry_after = int(info['reset_time'] - time.time())
            print(f"            Rate limit exceeded. Retry after {retry_after} seconds.")
    
    # Example 4: Demonstrate configuration
    print("\n=== Rate Limit Configuration ===\n")
    
    config = RateLimitConfig()
    
    print("Default rate limits by tier:")
    for tier in SubscriptionTier:
        print(f"  {tier.value.upper()}:")
        for window, limit in config.DEFAULT_LIMITS[tier].items():
            print(f"    {window.value}: {limit:,} requests")
    
    print("\nEndpoint multipliers:")
    for endpoint, multiplier in config.ENDPOINT_MULTIPLIERS.items():
        print(f"  {endpoint}: {multiplier}x")
    
    # Cleanup
    print("\n=== Cleanup ===\n")
    
    # Clean up test keys
    pattern = "rate_limit:*test*"
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)
        print(f"✓ Cleaned up {len(keys)} test keys")
    else:
        print("✓ No test keys to clean up")
    
    redis_client.close()
    print("✓ Redis connection closed")

def example_middleware_integration():
    """Example of how to integrate rate limiting middleware"""
    
    print("\n=== Middleware Integration Example ===\n")
    
    example_code = '''
# In your FastAPI app (main.py):

import redis
from fastapi import FastAPI
from app.middleware.rate_limiter import RateLimitMiddleware
from app.core.config import settings

# Create Redis client
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

# Create FastAPI app
app = FastAPI()

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    redis_client=redis_client,
    exempt_paths={"/health", "/docs", "/metrics"},
    exempt_ips={"127.0.0.1", "::1"},
    fail_open=True,  # Allow requests if Redis is down
    log_violations=True
)

# Your routes will now be automatically rate limited
@app.get("/api/v1/chatbot")
async def chatbot_endpoint():
    return {"message": "This endpoint is rate limited"}
    '''
    
    print(example_code)

def example_custom_rate_limits():
    """Example of setting custom rate limits per tenant"""
    
    print("\n=== Custom Rate Limits Example ===\n")
    
    example_code = '''
# Example: Custom rate limits for specific tenants
# You can store these in your database and override defaults

custom_limits = {
    "premium-tenant-123": {
        "tier": "enterprise",
        "custom_limits": {
            "minute": {"/api/v1/chatbot": 5000},  # 5x normal limit
            "hour": {"/api/v1/analytics": 25000}, # 5x normal limit
        }
    },
    "limited-tenant-456": {
        "tier": "starter", 
        "custom_limits": {
            "minute": {"/api/v1/chatbot": 10},    # 1/10th normal limit
        }
    }
}

# In your rate limiter, you would check for custom limits first:
def get_custom_limit(tenant_id: str, tier: SubscriptionTier, 
                    window: RateLimitWindow, endpoint: str) -> Optional[int]:
    if tenant_id in custom_limits:
        custom = custom_limits[tenant_id]["custom_limits"]
        return custom.get(window.value, {}).get(endpoint)
    return None
    '''
    
    print(example_code)

def example_monitoring_and_alerts():
    """Example of monitoring rate limit violations"""
    
    print("\n=== Monitoring and Alerts Example ===\n")
    
    example_code = '''
# Example: Set up monitoring for rate limit violations
import logging

# Configure structured logging
logger = logging.getLogger("rate_limiter")

# In your middleware, violations are logged like this:
def log_rate_limit_violation(tenant_id: str, endpoint: str, 
                           current_count: int, limit: int):
    logger.warning(
        "Rate limit exceeded",
        extra={
            "event": "rate_limit_violation",
            "tenant_id": tenant_id,
            "endpoint": endpoint,
            "current_count": current_count,
            "limit": limit,
            "timestamp": time.time()
        }
    )

# You can then set up alerts based on these logs:
# - CloudWatch/DataDog alerts for high violation rates
# - Slack/email notifications for specific tenants
# - Dashboard metrics for rate limiting effectiveness
    '''
    
    print(example_code)

if __name__ == "__main__":
    print("Ravian Backend API - Rate Limiting Examples")
    print("=" * 50)
    
    # Run async examples
    asyncio.run(example_rate_limiting())
    
    # Show integration examples
    example_middleware_integration()
    example_custom_rate_limits()
    example_monitoring_and_alerts()
    
    print("\n" + "=" * 50)
    print("Examples completed! Check the output above for details.")
