"""
Standardized exception classes and error response formatting
"""
from fastapi import HTTPException, status
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseAPIException(HTTPException):
    """Base exception class for API errors"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code or self.__class__.__name__
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class ValidationError(BaseAPIException):
    """Validation error - 400 Bad Request"""
    def __init__(self, detail: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code
        )


class AuthenticationError(BaseAPIException):
    """Authentication error - 401 Unauthorized"""
    def __init__(self, detail: str = "Authentication required", error_code: str = "AUTH_REQUIRED"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(BaseAPIException):
    """Authorization error - 403 Forbidden"""
    def __init__(self, detail: str = "Access denied", error_code: str = "ACCESS_DENIED"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code
        )


class NotFoundError(BaseAPIException):
    """Resource not found - 404 Not Found"""
    def __init__(self, resource: str = "Resource", error_code: str = "NOT_FOUND"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} not found",
            error_code=error_code
        )


class ConflictError(BaseAPIException):
    """Resource conflict - 409 Conflict"""
    def __init__(self, detail: str, error_code: str = "CONFLICT"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code=error_code
        )


class InternalServerError(BaseAPIException):
    """Internal server error - 500"""
    def __init__(self, detail: str = "Internal server error", error_code: str = "INTERNAL_ERROR"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code
        )


def create_error_response(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standardized error response format.
    
    Args:
        status_code: HTTP status code
        message: Error message
        error_code: Machine-readable error code
        details: Additional error details
        
    Returns:
        Standardized error response dictionary
    """
    response = {
        "error": {
            "code": error_code or "UNKNOWN_ERROR",
            "message": message,
            "status_code": status_code
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    return response
