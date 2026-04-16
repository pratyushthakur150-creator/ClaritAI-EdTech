import logging
import sys
import time
import asyncio
from contextlib import asynccontextmanager
from typing import List

import redis
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.middleware.auth import JWTAuthenticationMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.routers.health import router as health_router
from app.routers.v1 import api_router as v1_api_router

# Configure logging so logs always appear in the terminal (force=True for uvicorn --reload)
LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
LOG_LEVEL = getattr(logging, settings.log_level.upper(), logging.INFO)
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, stream=sys.stderr, force=True)
logger = logging.getLogger(__name__)
logger.info("Logging configured for terminal output (level=%s)", settings.log_level)

# Global Redis client
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global redis_client
    
    # Startup
    logger.info("Starting up Ravian Backend API...")
    
    try:
        # Initialize Redis connection with short timeout to avoid hanging
        redis_timeout = getattr(settings, 'redis_timeout', 2)  # Use 2 seconds max
        redis_client = None
        
        try:
            redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password if settings.redis_password else None,
                ssl=settings.redis_ssl,
                max_connections=getattr(settings, 'redis_pool_size', 50),
                socket_timeout=redis_timeout,
                socket_connect_timeout=redis_timeout,  # Short connect timeout
                decode_responses=True,
                retry_on_timeout=False,  # Don't retry on timeout
                health_check_interval=30
            )
            
            # Test Redis connection with timeout
            await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, redis_client.ping),
                timeout=redis_timeout
            )
            logger.info("✓ Redis connection established")
            app.state.redis = redis_client
            
        except (asyncio.TimeoutError, redis.RedisError, ConnectionError, OSError) as e:
            logger.warning(f"⚠ Redis connection failed (will continue without Redis): {e}")
            redis_client = None
            if not settings.rate_limit_fail_open:
                logger.error("Rate limiting required but Redis unavailable - startup may fail")
            else:
                logger.info("Continuing without Redis - rate limiting disabled")
        
        logger.info("✓ Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"✗ Application startup failed: {e}")
        if not settings.rate_limit_fail_open:
            raise
        else:
            logger.warning("Continuing despite startup error due to fail_open setting")
            redis_client = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down Ravian Backend API...")
    
    try:
        if redis_client:
            redis_client.close()
            logger.info("✓ Redis connection closed")
    except Exception as e:
        logger.error(f"✗ Error during shutdown: {e}")
    
    logger.info("✓ Application shutdown completed")

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
    redirect_slashes=False
)

# Add security middleware
if settings.https_only:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts.split(",") if isinstance(settings.allowed_hosts, str) else settings.allowed_hosts
    )

# Add JWT authentication middleware
app.add_middleware(
    JWTAuthenticationMiddleware,
    public_paths=[ 
        "/health", 
        "/health/detailed", 
        "/docs", 
        "/redoc", 
        "/openapi.json",
        "/favicon.ico",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/context/health",
        "/api/v1/chatbot/*",
        "/api/v1/content/*",       # All content endpoints public (testing)
        "/content-debug",  # Alternative public debug (no /api/v1)
        "/static/*",               # TTS audio files (browser <audio> can't send JWT)
    ]
)

# Add rate limiting middleware.
# NOTE: In FastAPI, middleware executes in reverse order of registration.
# We register auth middleware BEFORE rate limiting so rate limiting runs before auth.
if settings.rate_limit_enabled and redis_client:
    app.add_middleware(
        RateLimitMiddleware,
        redis_client=redis_client,
        exempt_paths=set(settings.rate_limit_exempt_paths.split(",")) if isinstance(settings.rate_limit_exempt_paths, str) else set(settings.rate_limit_exempt_paths),
        exempt_ips=set(settings.rate_limit_exempt_ips.split(",")) if isinstance(settings.rate_limit_exempt_ips, str) else set(settings.rate_limit_exempt_ips),
        exempt_user_agents=set(settings.rate_limit_exempt_user_agents.split(",")) if isinstance(settings.rate_limit_exempt_user_agents, str) else set(settings.rate_limit_exempt_user_agents),
        fail_open=settings.rate_limit_fail_open,
        log_violations=settings.rate_limit_log_violations
    )
    logger.info("✓ Rate limiting middleware enabled")
else:
    logger.warning("⚠ Rate limiting middleware disabled")

# Add CORS middleware LAST in code so it runs FIRST and always adds headers,
# even on 401/403 responses returned by auth middleware.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8080"],
    allow_origin_regex=".*", # Allow widgets from any site (SSSi, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request and response to the terminal."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        method = request.method
        path = request.url.path
        logger.info("--> %s %s", method, path)
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("<-- %s %s %s %.1fms", method, path, response.status_code, duration_ms)
        return response


app.add_middleware(RequestLoggingMiddleware)

# Public debug endpoint (no auth) - verify content router version
@app.get("/content-debug", tags=["Diagnostic"])
async def content_debug_public():
    """Public endpoint to verify content router has no permission checks."""
    logger.info("[CONTENT-DEBUG] /content-debug hit - returning 200")
    return {
        "status": "content_router_v2",
        "permission_checks": "NONE",
        "message": "Content router loaded - all authenticated users allowed",
    }

# Include routers
app.include_router(health_router, prefix="", tags=["Health"])

# API v1 routes (single mount; all v1 routers + prefixes defined in app/routers/v1/__init__.py)
app.include_router(v1_api_router, prefix="/api/v1")

# Serve TTS audio files (and any other static assets)
# Must be AFTER all router includes — mounts are catch-all and would shadow API routes.
import os as _os
_static_tts_dir = _os.path.join("static", "audio", "tts")
_os.makedirs(_static_tts_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
logger.info("✓ Static files mounted at /static (TTS dir: %s)", _static_tts_dir)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Ravian Backend API",
        "version": settings.api_version,
        "status": "operational",
        "docs_url": "/docs" if settings.debug else "Contact administrator for API documentation",
        "health_check": "/health"
    }

# Rate limit status endpoint (for monitoring)
@app.get("/api/v1/rate-limit/status", tags=["Rate Limiting"])
async def get_rate_limit_status():
    """Get current rate limit status (requires authentication)"""
    return {
        "message": "Rate limit status endpoint",
        "note": "Implementation depends on authentication middleware"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )
