"""
JWT Authentication Utilities

This module provides core JWT token handling functionality including:
- Token encoding/decoding
- Token validation and verification
- Claims extraction (user_id, tenant_id, roles)
- Security utilities
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, InvalidSignatureError
from pydantic import ValidationError

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class JWTError(Exception):
    """Base JWT error"""
    pass


class TokenExpiredError(JWTError):
    """Token has expired"""
    pass


class TokenInvalidError(JWTError):
    """Token is invalid"""
    pass


class TokenNotFoundError(JWTError):
    """Token not found in request"""
    pass


class JWTHandler:
    """JWT token handler with multi-tenant support"""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days
        
    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        role: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create JWT access token with user and tenant claims"""
        try:
            now = datetime.now(timezone.utc)
            expire = now + timedelta(minutes=self.access_token_expire_minutes)
            
            payload = {
                "sub": user_id,  # Subject (user ID)
                "tenant_id": tenant_id,
                "role": role,
                "token_type": "access",
                "iat": now,
                "exp": expire,
                "nbf": now  # Not before
            }
            
            # Add additional claims if provided
            if additional_claims:
                payload.update(additional_claims)
                
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Created access token for user {user_id} in tenant {tenant_id}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}", exc_info=True)
            raise JWTError(f"Failed to create access token: {str(e)}")
    
    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: str
    ) -> str:
        """Create JWT refresh token"""
        try:
            now = datetime.now(timezone.utc)
            expire = now + timedelta(days=self.refresh_token_expire_days)
            
            payload = {
                "sub": user_id,
                "tenant_id": tenant_id,
                "token_type": "refresh",
                "iat": now,
                "exp": expire,
                "nbf": now
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Created refresh token for user {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating refresh token: {str(e)}", exc_info=True)
            raise JWTError(f"Failed to create refresh token: {str(e)}")
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True, "verify_iat": True, "verify_nbf": True}
            )
            
            # Validate required claims
            required_claims = ["sub", "tenant_id", "token_type", "exp", "iat"]
            for claim in required_claims:
                if claim not in payload:
                    raise TokenInvalidError(f"Missing required claim: {claim}")
            
            logger.debug(f"Successfully decoded token for user {payload.get('sub')}")
            return payload
            
        except ExpiredSignatureError:
            logger.warning("Token has expired")
            raise TokenExpiredError("Token has expired")
            
        except InvalidSignatureError:
            logger.warning("Invalid token signature")
            raise TokenInvalidError("Invalid token signature")
            
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise TokenInvalidError(f"Invalid token: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error decoding token: {str(e)}", exc_info=True)
            raise TokenInvalidError(f"Error decoding token: {str(e)}")
    
    def extract_claims(self, token: str) -> Dict[str, Any]:
        """Extract claims from token without validation (for debugging)"""
        try:
            # Decode without verification for claim inspection
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception as e:
            logger.error(f"Error extracting claims: {str(e)}", exc_info=True)
            return {}
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash using bcrypt directly"""
        try:
            password_bytes = plain_password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}", exc_info=True)
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Hash password using bcrypt directly"""
        try:
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Password hashing error: {str(e)}", exc_info=True)
            raise JWTError(f"Failed to hash password: {str(e)}")




# Standalone password hashing functions for convenience
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return jwt_handler.get_password_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return jwt_handler.verify_password(plain_password, hashed_password)

# Global JWT handler instance
jwt_handler = JWTHandler()


def extract_token_from_header(authorization: str) -> str:
    """Extract Bearer token from Authorization header"""
    if not authorization:
        raise TokenNotFoundError("Authorization header is missing")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise TokenInvalidError("Invalid authorization header format")
    
    return parts[1]


def validate_tenant_access(token_tenant_id: str, requested_tenant_id: Optional[str] = None) -> bool:
    """Validate tenant access permissions"""
    if not requested_tenant_id:
        return True  # No specific tenant requested
    
    return token_tenant_id == requested_tenant_id


def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted (placeholder for Redis implementation)"""
    # TODO: Implement Redis blacklist check
    # redis_client.sismember("blacklisted_tokens", token)
    return False


def blacklist_token(token: str, expire_time: Optional[datetime] = None) -> bool:
    """Add token to blacklist (placeholder for Redis implementation)"""
    try:
        # TODO: Implement Redis blacklist
        # if expire_time:
        #     ttl = int((expire_time - datetime.now(timezone.utc)).total_seconds())
        #     redis_client.setex(f"blacklist:{token}", ttl, "1")
        logger.info("Token blacklisted (placeholder)")
        return True
    except Exception as e:
        logger.error(f"Error blacklisting token: {str(e)}", exc_info=True)
        return False


