"""
JWT Authentication Middleware

This middleware handles:
- JWT token validation from Authorization header
- User and tenant context injection
- Authentication bypass for public routes
- Proper error responses for auth failures
"""

from typing import List, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import json

from app.core.auth import (
    jwt_handler, 
    extract_token_from_header,
    JWTError,
    TokenExpiredError,
    TokenInvalidError,
    TokenNotFoundError,
    is_token_blacklisted,
    validate_tenant_access
)
from app.schemas.auth import UserContext, TenantContext
import logging

logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware:
    """
    JWT Authentication Middleware for multi-tenant architecture.

    Implemented as a pure ASGI middleware (not BaseHTTPMiddleware) to ensure:
    - Response headers are preserved on short-circuit 401/403 responses
    - Outer middleware like CORSMiddleware can always add CORS headers
    """

    def __init__(self, app, public_paths: Optional[List[str]] = None):
        self.app = app
        self.public_paths = public_paths or [
            "/health",
            "/health/detailed",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
        ]
        logger.info(f"JWT middleware initialized with {len(self.public_paths)} public paths: {sorted(self.public_paths)}")

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        # Very first check: bypass /content-debug using only scope (no Request yet)
        scope_path = (scope.get("path") or "").strip().lower()
        if "content-debug" in scope_path or scope_path.rstrip("/") in ("/content-debug", "/api/v1/content/debug", "/api/v1/content/health"):
            await self.app(scope, receive, send)
            return

        # Bypass auth for TTS audio files (browser <audio> element can't send JWT headers)
        if "/teaching-assistant/audio/" in scope_path or scope_path.startswith("/static/"):
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        path = scope.get("path", "")
        # Use both scope path and request.url.path (can differ with root_path/mounts)
        url_path = getattr(request.url, "path", "") or path
        method = request.method

        # Log every request (print ensures visibility in terminal)
        msg = f"[AUTH] {method} {path}"
        logger.info(msg)
        print(msg)

        # Skip auth for OPTIONS requests (CORS preflight)
        if method == "OPTIONS":
            logger.info(f"[AUTH] OPTIONS request - bypassing")
            await self.app(scope, receive, send)
            return

        def _path_is_content_public(p: str) -> bool:
            if not p:
                return False
            pl = (p.strip().rstrip("/") or "/").lower()
            return (
                pl in ("/content-debug", "/api/v1/content/debug", "/api/v1/content/health")
                or pl.endswith("/content-debug")
                or pl.endswith("/api/v1/content/debug")
                or pl.endswith("/api/v1/content/health")
                or "/content-debug" in pl
                or "/api/v1/content/debug" in pl
                or "/api/v1/content/health" in pl
            )

        # Explicit early bypass for content-debug and content health (check both path sources)
        has_auth_header = bool((request.headers.get("Authorization") or "").strip())
        if _path_is_content_public(path) or _path_is_content_public(url_path):
            logger.info(f"[AUTH] Bypassing auth for public path (early): scope_path={repr(path)} url_path={repr(url_path)}")
            await self.app(scope, receive, send)
            return
        if not has_auth_header and ("content-debug" in (path or "").lower() or "content-debug" in (url_path or "").lower()):
            logger.info(f"[AUTH] Bypassing auth (no auth header + content-debug): path={repr(path)} url_path={repr(url_path)}")
            await self.app(scope, receive, send)
            return

        is_public = self._is_public_path(path)
        msg = f"[AUTH] path='{path}' is_public={is_public}"
        logger.info(msg)
        print(msg)

        # Skip authentication for public paths, but still try to extract
        # user context if a JWT token is present (so tenant_id flows through).
        if is_public:
            print(f"[AUTH] BYPASSING auth for public path: {path}")
            logger.info(f"[AUTH] Bypassing auth for public path: {path}")

            # Opportunistic JWT decode — don't fail if absent/invalid
            try:
                token = self._extract_token(request)
                user_context, tenant_context = await self._authenticate_token(token)
                state = scope.setdefault("state", {})
                state["current_user"] = user_context
                state["current_tenant"] = tenant_context
                state["is_authenticated"] = True
                logger.info(
                    f"[AUTH] Public path with valid JWT — user {user_context.user_id} tenant {tenant_context.tenant_id}"
                )
            except Exception:
                # No token or invalid token — that's fine for public paths
                pass

            await self.app(scope, receive, send)
            return

        try:
            token = self._extract_token(request)
            user_context, tenant_context = await self._authenticate_token(token)

            # Inject context into request state (stored on scope["state"])
            state = scope.setdefault("state", {})
            state["current_user"] = user_context
            state["current_tenant"] = tenant_context
            state["is_authenticated"] = True

            logger.info(
                f"[AUTH] Authenticated user {user_context.user_id} tenant {tenant_context.tenant_id}"
            )

            await self.app(scope, receive, send)
            return

        except TokenNotFoundError as e:
            print(f"[AUTH] 401 TokenNotFoundError path='{path}' - NO AUTH HEADER")
            logger.info(f"[AUTH] 401 TokenNotFoundError for {path}: {e}")
            response = self._create_error_response(
                request=request,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Authentication required",
                error_code="AUTH_REQUIRED",
            )
        except TokenExpiredError as e:
            logger.info(f"[AUTH] 401 TokenExpiredError for {path}: {e}")
            response = self._create_error_response(
                request=request,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Token has expired",
                error_code="TOKEN_EXPIRED",
            )
        except TokenInvalidError as e:
            logger.info(f"[AUTH] 401 TokenInvalidError for {path}: {e}")
            response = self._create_error_response(
                request=request,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message=f"Invalid token: {str(e)}",
                error_code="TOKEN_INVALID",
            )
        except JWTError as e:
            logger.warning(f"JWT authentication error: {str(e)}")
            response = self._create_error_response(
                request=request,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Authentication failed",
                error_code="AUTH_FAILED",
            )
        except Exception as e:
            logger.error(f"Unexpected authentication error: {str(e)}", exc_info=True)
            response = self._create_error_response(
                request=request,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Internal authentication error",
                error_code="AUTH_ERROR",
            )

        await response(scope, receive, send)
        return
    
    def _is_public_path(self, path: str) -> bool:
        """
        Check if path is in public paths list.
        Supports exact match, trailing slash normalization, and wildcard patterns.
        """
        # Normalize path (remove trailing slash except for root)
        path_normalized = (path or "").strip().rstrip("/") or "/"

        # Convert to set for fast lookup (handles list or set from caller)
        public_set = set(self.public_paths) if self.public_paths else set()

        # Exact match (fast path)
        if path_normalized in public_set:
            print(f"[AUTH] EXACT MATCH path='{path_normalized}'")
            return True

        # Also try with trailing slash
        path_with_slash = path_normalized + "/" if path_normalized != "/" else "/"
        if path_with_slash in public_set:
            print(f"[AUTH] EXACT MATCH (with slash) path='{path_with_slash}'")
            return True

        # Wildcard matching (e.g., /api/v1/content/*)
        for public_path in public_set:
            if public_path.endswith("/*"):
                # Remove /* to get the prefix
                prefix = public_path[:-2]  # "/api/v1/content/*" -> "/api/v1/content"

                # Check if normalized path starts with this prefix
                if path_normalized.startswith(prefix):
                    # Ensure it's a proper path segment match
                    # /api/v1/content/index -> YES
                    # /api/v1/content-other/foo -> NO
                    if len(path_normalized) == len(prefix) or path_normalized[len(prefix):].startswith("/"):
                        print(f"[AUTH] WILDCARD MATCH pattern='{public_path}' path='{path_normalized}'")
                        return True

        # Content fallback (hardcoded for debugging - remove after testing)
        content_paths = ["/content-debug", "/api/v1/content/debug", "/api/v1/content/health"]
        if path_normalized in content_paths:
            print(f"[AUTH] FALLBACK MATCH (content debug) path='{path_normalized}'")
            return True

        # No match
        print(f"[AUTH] NO MATCH path='{path_normalized}' repr={repr(path_normalized)}")
        return False
    
    def _extract_token(self, request: Request) -> str:
        """Extract JWT token from request Authorization header"""
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise TokenNotFoundError("Authorization header missing")
        
        return extract_token_from_header(authorization)
    
    async def _authenticate_token(self, token: str) -> tuple[UserContext, TenantContext]:
        """Authenticate token and return user and tenant contexts"""
        
        # Check if token is blacklisted
        if is_token_blacklisted(token):
            raise TokenInvalidError("Token has been revoked")
        
        # Decode and validate token
        payload = jwt_handler.decode_token(token)
        
        # Validate token type
        if payload.get("token_type") != "access":
            raise TokenInvalidError("Invalid token type")
        
        # Extract user and tenant information
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        role = payload.get("role", "user")
        
        if not user_id or not tenant_id:
            raise TokenInvalidError("Token missing required user or tenant information")
        
        # Create context objects
        user_context = UserContext(
            user_id=user_id,
            role=role,
            tenant_id=tenant_id,
            token_payload=payload
        )
        
        tenant_context = TenantContext(
            tenant_id=tenant_id,
            # Additional tenant info can be fetched from database here
        )
        
        return user_context, tenant_context
    
    def _create_error_response(self, request: Request, status_code: int, message: str, error_code: str) -> JSONResponse:
        """Create standardized error response."""
        error_response = {
            "error": {
                "code": error_code,
                "message": message,
                "status_code": status_code
            }
        }

        return JSONResponse(
            status_code=status_code,
            content=error_response,
            headers={"WWW-Authenticate": "Bearer"}
        )


class OptionalJWTMiddleware(BaseHTTPMiddleware):
    """Optional JWT middleware that doesn't require authentication"""
    
    async def dispatch(self, request: Request, call_next):
        """Process request with optional authentication"""
        try:
            authorization = request.headers.get("Authorization")
            if authorization:
                token = extract_token_from_header(authorization)
                
                if not is_token_blacklisted(token):
                    payload = jwt_handler.decode_token(token)
                    
                    user_context = UserContext(
                        user_id=payload.get("sub"),
                        role=payload.get("role", "user"),
                        tenant_id=payload.get("tenant_id"),
                        token_payload=payload
                    )
                    
                    tenant_context = TenantContext(
                        tenant_id=payload.get("tenant_id")
                    )
                    
                    request.state.current_user = user_context
                    request.state.current_tenant = tenant_context
                    request.state.is_authenticated = True
                    
                    logger.debug(f"Optional auth: authenticated user {user_context.user_id}")
                else:
                    request.state.is_authenticated = False
            else:
                request.state.is_authenticated = False
                
        except Exception as e:
            logger.debug(f"Optional auth error (ignored): {str(e)}")
            request.state.is_authenticated = False
        
        return await call_next(request)
