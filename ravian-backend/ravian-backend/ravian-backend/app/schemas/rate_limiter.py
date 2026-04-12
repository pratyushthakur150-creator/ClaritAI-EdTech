
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class SubscriptionTier(str, Enum):
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"

class RateLimitWindow(str, Enum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"

class RateLimitInfo(BaseModel):
    """Rate limit information returned with responses"""
    limit: int = Field(..., description="Maximum requests allowed in window")
    remaining: int = Field(..., description="Remaining requests in current window")
    reset_time: float = Field(..., description="Unix timestamp when window resets")
    window: str = Field(..., description="Time window (minute/hour/day)")
    current_count: int = Field(default=0, description="Current request count in window")
    window_size: int = Field(..., description="Window size in seconds")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    tier: Optional[str] = Field(None, description="Subscription tier")
    endpoint: Optional[str] = Field(None, description="API endpoint")
    redis_error: bool = Field(default=False, description="Whether Redis error occurred")

class RateLimitHeaders(BaseModel):
    """HTTP headers for rate limiting"""
    x_ratelimit_limit: str = Field(..., description="Rate limit")
    x_ratelimit_remaining: str = Field(..., description="Remaining requests")
    x_ratelimit_reset: str = Field(..., description="Reset timestamp")
    x_ratelimit_window: str = Field(..., description="Time window")
    retry_after: Optional[str] = Field(None, description="Retry after seconds")

class RateLimitStatus(BaseModel):
    """Current rate limit status for a tenant/endpoint"""
    tenant_id: str
    tier: SubscriptionTier
    endpoint: str
    windows: Dict[str, RateLimitInfo]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RateLimitViolation(BaseModel):
    """Rate limit violation event for logging/monitoring"""
    tenant_id: str
    user_id: Optional[str] = None
    tier: SubscriptionTier
    endpoint: str
    window: RateLimitWindow
    limit: int
    current_count: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None

class RateLimitConfig(BaseModel):
    """Rate limit configuration"""
    enabled: bool = Field(default=True, description="Enable rate limiting")
    algorithm: str = Field(default="sliding_window", description="Rate limiting algorithm")
    fail_open: bool = Field(default=True, description="Allow requests when Redis is down")
    redis_timeout: int = Field(default=5, description="Redis operation timeout")
    log_violations: bool = Field(default=True, description="Log rate limit violations")
    exempt_ips: List[str] = Field(default=[], description="IP addresses exempt from rate limiting")
    exempt_user_agents: List[str] = Field(default=[], description="User agents exempt from rate limiting")

class TenantRateLimitOverride(BaseModel):
    """Override rate limits for specific tenant"""
    tenant_id: str
    tier: SubscriptionTier
    custom_limits: Optional[Dict[str, Dict[str, int]]] = None  # {window: {endpoint: limit}}
    exempt: bool = Field(default=False, description="Exempt from all rate limiting")
    notes: Optional[str] = None

class RateLimitResponse(BaseModel):
    """Rate limit exceeded response"""
    error: str = Field(default="Rate limit exceeded")
    message: str
    limit: int
    window: str
    reset_time: float
    retry_after: int
    tenant_id: Optional[str] = None
    endpoint: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Rate limit exceeded",
                "message": "Too many requests. Rate limit of 100 requests per minute exceeded.",
                "limit": 100,
                "window": "minute",
                "reset_time": 1640995200.0,
                "retry_after": 45,
                "tenant_id": "tenant-123",
                "endpoint": "/api/v1/chatbot"
            }
        }

class RateLimitMetrics(BaseModel):
    """Rate limiting metrics for monitoring"""
    tenant_id: str
    endpoint: str
    window: str
    total_requests: int
    allowed_requests: int
    blocked_requests: int
    success_rate: float
    avg_remaining: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
