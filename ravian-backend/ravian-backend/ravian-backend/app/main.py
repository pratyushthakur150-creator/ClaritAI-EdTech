import logging
import sys
import time
import asyncio
from contextlib import asynccontextmanager
from typing import List

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.middleware.auth import JWTAuthenticationMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.routers.health import router as health_router
from app.routers.v1 import api_router as v1_api_router
from app.routers.v1 import usage, workflows

# Configure logging so logs always appear in the terminal
LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
LOG_LEVEL = getattr(logging, settings.log_level.upper(), logging.INFO)
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, stream=sys.stderr, force=True)
logger = logging.getLogger(__name__)
logger.info("Logging configured for terminal output (level=%s)", settings.log_level)

# Global Redis client (may be real Redis or MockRedis)
redis_client = get_redis_client()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with optional Redis."""
    global redis_client
    
    logger.info("Starting up Ravian Backend API...")
    
    # Auto-create database tables on startup
    try:
        from app.core.database import create_tables
        create_tables()
        logger.info("✓ Database tables created/verified")
    except Exception as e:
        logger.error(f"✗ Failed to create database tables: {e}")
    
    try:
        # Try Redis but don't crash if it fails
        if hasattr(redis_client, "ping"):
            await asyncio.get_event_loop().run_in_executor(None, redis_client.ping)
            logger.info("✓ Redis connection available")
            app.state.redis = redis_client
        else:
            logger.warning("Redis client not available; proceeding without Redis")
    except Exception as e:
        logger.warning(f"Redis ping failed: {e}")

    # Groq API is used for Whisper — no local model to pre-load
    logger.info("✓ Using Groq API for Whisper transcription (no local model needed)")
    app.state.whisper_model = None

    # ── Auto-load exam knowledge into ChromaDB for Aria chatbot RAG ──
    try:
        from app.rag.chatbot_rag.exam_knowledge_loader import load_all_exams
        logger.info("Loading exam knowledge into ChromaDB...")
        rag_results = await load_all_exams()
        loaded = [k for k, v in rag_results.items() if v]
        failed = [k for k, v in rag_results.items() if not v]
        logger.info(f"✓ Exam knowledge loaded: {loaded}")
        if failed:
            logger.warning(f"⚠ Failed to load: {failed}")
    except Exception as e:
        logger.warning(f"⚠ Exam knowledge loading failed (non-critical): {e}")

    yield
    
    logger.info("Shutting down Ravian Backend API...")
    
    try:
        if redis_client and hasattr(redis_client, "close"):
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
    redirect_slashes=True
)

# Add security middleware
if settings.https_only:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts
    )

# Add JWT authentication middleware first in code (runs after CORS).
app.add_middleware(
    JWTAuthenticationMiddleware,
    public_paths={
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
        "/api/v1/chatbot/message",
        "/api/v1/chatbot/capture-lead",
        "/api/v1/chatbot/config",
        "/content-debug",          # Alternative public debug (no /api/v1)
        "/chatbot-demo",           # Chatbot widget demo page (no auth)
        "/aria-demo",              # Aria lead-capture chatbot demo (no auth)
        "/static/*",               # TTS audio files (browser <audio> can't send JWT)
        "/api/v1/teaching-assistant/audio/*",  # TTS audio endpoint
        # --- Data endpoints (public for dev/demo) ---
        "/api/v1/dashboard/*",
        "/api/v1/students",
        "/api/v1/leads/*",
        "/api/v1/leads",
        "/api/v1/calls/*",
        "/api/v1/calls",
        "/api/v1/demos/*",
        "/api/v1/demos",
        "/api/v1/enrollments/*",
        "/api/v1/enrollments",
        "/api/v1/voice/*",
        "/api/v1/teaching-assistant/*",
        "/api/v1/chatbot/*",
    }
)

# Rate limiting middleware DISABLED - BaseHTTPMiddleware deadlocks with sync endpoints
# TODO: Convert to pure ASGI middleware (like JWTAuthenticationMiddleware) to re-enable
# if settings.rate_limit_enabled and redis_client:
#     app.add_middleware(
#         RateLimitMiddleware,
#         redis_client=redis_client,
#         exempt_paths=set(settings.rate_limit_exempt_paths),
#         exempt_ips=set(settings.rate_limit_exempt_ips),
#         exempt_user_agents=set(settings.rate_limit_exempt_user_agents),
#         fail_open=settings.rate_limit_fail_open,
#         log_violations=settings.rate_limit_log_violations
#     )
#     logger.info("✓ Rate limiting middleware enabled")
logger.info("⚠ Rate limiting middleware disabled (BaseHTTPMiddleware incompatible with sync endpoints)")

# Add CORS middleware LAST in code so it runs FIRST and adds headers even on 401/403.
# CORS origins: use CORS_ORIGINS env var (comma-separated) or fallback to localhost
_cors_raw = getattr(settings, 'cors_origins', None) or ""
if isinstance(_cors_raw, list):
    _cors_origins = _cors_raw
else:
    _cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()] if _cors_raw else ["http://localhost:3000", "http://127.0.0.1:3000"]

# When wildcard "*" is used, FastAPI requires allow_credentials=False
_cors_allow_all = "*" in _cors_origins
if _cors_allow_all:
    _cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=not _cors_allow_all,  # Must be False when origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request (method, path, query, body, client IP) and response status."""

    # Paths to skip body logging (too noisy / binary)
    _SKIP_BODY_PATHS = {"/health", "/favicon.ico"}
    # Content types we will try to log as text
    _TEXT_TYPES = ("application/json", "text/plain", "application/x-www-form-urlencoded")

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        method  = request.method
        path    = request.url.path
        query   = str(request.url.query) if request.url.query else ""
        client  = request.client.host if request.client else "unknown"

        # ── Log incoming request ──────────────────────────────────────
        query_display = f"?{query}" if query else ""
        logger.info("━━━ ▶ %s %s%s  [client=%s]", method, path, query_display, client)

        # Log request body for non-binary endpoints
        if path not in self._SKIP_BODY_PATHS and method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            is_multipart = "multipart/form-data" in content_type
            if not is_multipart:
                try:
                    body_bytes = await request.body()
                    if body_bytes:
                        body_str = body_bytes.decode("utf-8", errors="replace")
                        # Mask passwords in logs
                        import re
                        body_str = re.sub(r'(?i)("password"\s*:\s*")([^"]+)(")', r'\1***\3', body_str)
                        logger.info("    Body: %s", body_str[:500])
                except Exception:
                    pass
            else:
                logger.info("    Body: <multipart/form-data — file upload>")

        # ── Execute request ───────────────────────────────────────────
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        # ── Log response ──────────────────────────────────────────────
        status = response.status_code
        level  = logging.WARNING if status >= 400 else logging.INFO
        logger.log(level, "━━━ ◀ %s %s%s  %d  %.1fms", method, path, query_display, status, duration_ms)

        return response


app.add_middleware(RequestLoggingMiddleware)

# Teaching Assistant: static files for TTS audio
# Use absolute paths anchored to the backend root so they resolve correctly
# regardless of the working directory (fixes 404 with --reload).
import os
from pathlib import Path as _Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
_BACKEND_ROOT = _Path(__file__).resolve().parent.parent  # .../ravian-backend
_AUDIO_DIR = _BACKEND_ROOT / "storage" / "audio"
_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
(_AUDIO_DIR / "tts").mkdir(parents=True, exist_ok=True)
(_BACKEND_ROOT / "storage" / "documents").mkdir(parents=True, exist_ok=True)
(_BACKEND_ROOT / "chroma_db").mkdir(parents=True, exist_ok=True)
logger.info(f"Static audio directory: {_AUDIO_DIR}")
app.mount("/static/audio", StaticFiles(directory=str(_AUDIO_DIR)), name="audio")

# Chatbot demo page — served at /chatbot-demo
@app.get("/chatbot-demo", tags=["Chatbot Demo"])
async def chatbot_demo_page():
    """Serve the chatbot demo HTML page."""
    demo_path = os.path.join(os.path.dirname(__file__), "..", "static", "chatbot-demo.html")
    if os.path.exists(demo_path):
        return FileResponse(demo_path, media_type="text/html")
    return JSONResponse({"error": "Demo file not found"}, status_code=404)

# Aria lead-capture chatbot demo — served at /aria-demo
@app.get("/aria-demo", tags=["Aria Chatbot Demo"])
async def aria_demo_page():
    """Serve the Aria AI Academic Advisor chatbot demo (lead capture)."""
    demo_path = os.path.join(os.path.dirname(__file__), "..", "static", "aria-chatbot-demo.html")
    if os.path.exists(demo_path):
        return FileResponse(demo_path, media_type="text/html")
    return JSONResponse({"error": "Aria demo file not found"}, status_code=404)

# Include routers
app.include_router(health_router, prefix="", tags=["Health"])

# API v1 routes (single mount; all v1 routers + prefixes defined in app/routers/v1/__init__.py)
app.include_router(v1_api_router, prefix="/api/v1")
logger.info(f"V1 router mounted with {len(v1_api_router.routes)} total routes")
logger.info(f"  Routes include: {[r.path for r in v1_api_router.routes[:10]]}")

# Note: usage, workflows, test_minimal routers are already mounted via v1_api_router

# Public content debug (no auth)
@app.get("/content-debug", tags=["Diagnostic"])
async def content_debug_public():
    """Verify content router loaded - no auth required."""
    logger.info("[CONTENT-DEBUG] /content-debug hit - returning 200")
    return {"status": "content_router_v2", "permission_checks": "NONE"}

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
    # This would be implemented to show current rate limit status
    # for the authenticated tenant
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