
import time
import json
import logging
from typing import Optional, Set, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis
from redis import Redis

from app.core.rate_limiter import RateLimiter, SubscriptionTier
from app.schemas.rate_limiter import (
    RateLimitResponse, 
    RateLimitViolation, 
    RateLimitHeaders,
    RateLimitInfo
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis for per-tenant limits"""
    
    def __init__(
        self,
        app,
        redis_client: Redis,
        exempt_paths: Optional[Set[str]] = None,
        exempt_ips: Optional[Set[str]] = None,
        exempt_user_agents: Optional[Set[str]] = None,
        fail_open: bool = True,
        log_violations: bool = True
    ):
        super().__init__(app)
        self.redis_client = redis_client
        self.rate_limiter = RateLimiter(redis_client)
        self.fail_open = fail_open
        self.log_violations = log_violations
        
        # Default exempt paths (health checks, docs, static)
        self.exempt_paths = exempt_paths or {
            "/health",
            "/health/detailed",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        }
        
        self.exempt_ips = exempt_ips or set()
        self.exempt_user_agents = exempt_user_agents or set()
        
        # Add configured exemptions
        if hasattr(settings, 'RATE_LIMIT_EXEMPT_IPS'):
            self.exempt_ips.update(settings.RATE_LIMIT_EXEMPT_IPS)
        if hasattr(settings, 'RATE_LIMIT_EXEMPT_USER_AGENTS'):
            self.exempt_user_agents.update(settings.RATE_LIMIT_EXEMPT_USER_AGENTS)
    
    def _should_exempt_request(self, request: Request) -> tuple[bool, str]:
        """Check if request should be exempt from rate limiting"""
        
        # Check path exemptions
        path = request.url.path
        if path in self.exempt_paths:
            return True, f"exempt_path:{path}"
        
        # Check if path starts with exempt prefixes
        exempt_prefixes = ["/static", "/assets", "/favicon"]
        if any(path.startswith(prefix) for prefix in exempt_prefixes):
            return True, f"exempt_prefix:{path}"
        
        # Check IP exemptions
        client_ip = self._get_client_ip(request)
        if client_ip in self.exempt_ips:
            return True, f"exempt_ip:{client_ip}"
        
        # Check user agent exemptions
        user_agent = request.headers.get("user-agent", "")
        if any(exempt_ua in user_agent for exempt_ua in self.exempt_user_agents):
            return True, f"exempt_user_agent"
        
        # Check if user has admin role (if available in request state)
        if hasattr(request.state, 'user_context'):
            user_context = request.state.user_context
            role = getattr(user_context, 'role', None) or getattr(user_context, 'roles', [])
            if role == 'ADMIN' or (isinstance(role, list) and 'ADMIN' in role):
                return True, "exempt_admin_role"
        
        return False, ""
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take first IP in case of multiple proxies
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _get_tenant_info(self, request: Request) -> tuple[Optional[str], SubscriptionTier]:
        """Extract tenant ID and subscription tier from request"""
        
        # Try to get from JWT middleware state
        if hasattr(request.state, 'tenant_context'):
            tenant_context = request.state.tenant_context
            tenant_id = getattr(tenant_context, 'tenant_id', None)
            tier_str = getattr(tenant_context, 'subscription_tier', 'starter')
            
            try:
                tier = SubscriptionTier(tier_str.lower())
            except ValueError:
                tier = SubscriptionTier.STARTER
                logger.warning(f"Invalid subscription tier '{tier_str}' for tenant {tenant_id}, defaulting to starter")
            
            return tenant_id, tier
        
        # Fallback: try to get from headers
        tenant_id = request.headers.get("x-tenant-id")
        tier_header = request.headers.get("x-subscription-tier", "starter")
        
        try:
            tier = SubscriptionTier(tier_header.lower())
        except ValueError:
            tier = SubscriptionTier.STARTER
        
        return tenant_id, tier
    
    def _create_rate_limit_headers(self, limit_info: RateLimitInfo) -> Dict[str, str]:
        """Create HTTP headers for rate limiting"""
        headers = {
            "X-RateLimit-Limit": str(limit_info.limit),
            "X-RateLimit-Remaining": str(limit_info.remaining),
            "X-RateLimit-Reset": str(int(limit_info.reset_time)),
            "X-RateLimit-Window": limit_info.window
        }
        
        # Add retry-after header if limit exceeded
        if limit_info.remaining <= 0:
            retry_after = max(1, int(limit_info.reset_time - time.time()))
            headers["Retry-After"] = str(retry_after)
        
        return headers
    
    def _log_rate_limit_violation(
        self,
        request: Request,
        limit_info: RateLimitInfo,
        tenant_id: Optional[str],
        user_id: Optional[str]
    ):
        """Log rate limit violation for monitoring"""
        if not self.log_violations:
            return
        
        violation = RateLimitViolation(
            tenant_id=tenant_id or "unknown",
            user_id=user_id,
            tier=SubscriptionTier(limit_info.tier) if limit_info.tier else SubscriptionTier.STARTER,
            endpoint=limit_info.endpoint or request.url.path,
            window=limit_info.window,
            limit=limit_info.limit,
            current_count=limit_info.current_count,
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_id=request.headers.get("x-request-id")
        )
        
        logger.warning(
            f"Rate limit exceeded: {violation.json()}",
            extra={
                "event": "rate_limit_violation",
                "tenant_id": tenant_id,
                "endpoint": request.url.path,
                "window": limit_info.window,
                "current_count": limit_info.current_count,
                "limit": limit_info.limit
            }
        )
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiting middleware"""
        
        start_time = time.time()
        
        # Check if request should be exempt
        is_exempt, exempt_reason = self._should_exempt_request(request)
        if is_exempt:
            logger.debug(f"Request exempt from rate limiting: {exempt_reason}")
            response = await call_next(request)
            return response
        
        # Get tenant information
        tenant_id, subscription_tier = self._get_tenant_info(request)
        
        if not tenant_id:
            logger.debug("No tenant ID found, skipping rate limiting")
            if self.fail_open:
                response = await call_next(request)
                return response
            else:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Tenant ID required", "message": "Missing tenant identification"}
                )
        
        # Get user ID if available
        user_id = None
        if hasattr(request.state, 'user_context'):
            user_id = getattr(request.state.user_context, 'user_id', None)
        
        endpoint = request.url.path
        client_ip = self._get_client_ip(request)
        
        try:
            # Check rate limits
            allowed, limit_info = await self.rate_limiter.check_rate_limit(
                tenant_id=tenant_id,
                tier=subscription_tier,
                endpoint=endpoint,
                user_id=user_id,
                ip_address=client_ip
            )
            
            # Create rate limit headers
            headers = self._create_rate_limit_headers(limit_info)
            
            if not allowed:
                # Log violation
                self._log_rate_limit_violation(request, limit_info, tenant_id, user_id)
                
                # Create rate limit response
                retry_after = max(1, int(limit_info['reset_time'] - time.time()))
                
                rate_limit_response = RateLimitResponse(
                    message=f"Too many requests. Rate limit of {limit_info['limit']} requests per {limit_info['window']} exceeded.",
                    limit=limit_info['limit'],
                    window=limit_info['window'],
                    reset_time=limit_info['reset_time'],
                    retry_after=retry_after,
                    tenant_id=tenant_id,
                    endpoint=endpoint
                )
                
                return JSONResponse(
                    status_code=429,
                    content=rate_limit_response.dict(),
                    headers=headers
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            for key, value in headers.items():
                response.headers[key] = value
            
            # Add processing time
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiting: {e}")
            
            if self.fail_open:
                logger.warning("Redis error, failing open (allowing request)")
                response = await call_next(request)
                response.headers["X-RateLimit-Error"] = "Redis unavailable"
                return response
            else:
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "Service temporarily unavailable",
                        "message": "Rate limiting service is unavailable"
                    }
                )
        
        except Exception as e:
            logger.error(f"Unexpected error in rate limiting middleware: {e}")
            
            if self.fail_open:
                response = await call_next(request)
                return response
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal server error",
                        "message": "Rate limiting error"
                    }
                )

def create_rate_limit_middleware(
    redis_client: Redis,
    **kwargs
) -> RateLimitMiddleware:
    """Factory function to create rate limit middleware"""
    return RateLimitMiddleware(
        app=None,  # Will be set by FastAPI
        redis_client=redis_client,
        **kwargs
    )
