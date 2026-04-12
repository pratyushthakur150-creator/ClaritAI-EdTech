"""
Authentication Schemas

Pydantic models for authentication-related data structures:
- User and tenant contexts
- Token requests and responses
- Authentication payloads

UserContext and tokens use UPPERCASE roles to match PostgreSQL userrole enum.
"""

from datetime import datetime
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field, validator


class TokenBase(BaseModel):
    """Base token model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration


class TokenResponse(TokenBase):
    """Token response with optional refresh token"""
    refresh_token: Optional[str] = None
    user_id: str
    tenant_id: str
    role: str


class TokenRequest(BaseModel):
    """Token creation request"""
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)
    tenant_id: Optional[str] = None  # Can be extracted from username or provided


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., min_length=1)


class UserContext(BaseModel):
    """Current authenticated user context"""
    user_id: str
    role: str
    tenant_id: str
    permissions: List[str] = []
    token_payload: Dict[str, Any] = {}
    
    @validator('role')
    def validate_role(cls, v):
        # Match PostgreSQL userrole enum (UPPERCASE)
        allowed_roles = ['ADMIN', 'MENTOR', 'VIEWER']
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of {allowed_roles}')
        return v


class TenantContext(BaseModel):
    """Current tenant context"""
    tenant_id: str
    tenant_name: Optional[str] = None
    plan: Optional[str] = "free"  # free, pro, enterprise
    features: List[str] = []
    rate_limits: Dict[str, int] = {}
    
    @validator('plan')
    def validate_plan(cls, v):
        if v:
            allowed_plans = ['free', 'pro', 'enterprise']
            if v not in allowed_plans:
                raise ValueError(f'Plan must be one of {allowed_plans}')
        return v


class AuthenticationError(BaseModel):
    """Authentication error response"""
    error: str
    message: str
    status_code: int


class LoginRequest(BaseModel):
    """Login request payload"""
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    tenant_id: Optional[str] = None
    remember_me: bool = False


class RegisterRequest(BaseModel):
    """User registration request - uses UPPERCASE roles to match database"""
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    tenant_name: Optional[str] = Field(None, max_length=100)
    # ✅ FIXED: Role should be UPPERCASE to match PostgreSQL enum
    role: str = Field(default="VIEWER")
    
    @validator('role')
    def validate_role(cls, v):
        # Accept UPPERCASE roles that match database enum
        allowed_roles = ['ADMIN', 'MENTOR', 'VIEWER']
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of {allowed_roles}')
        return v


class LogoutRequest(BaseModel):
    """Logout request to blacklist token"""
    revoke_all_tokens: bool = False


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    tenant_id: Optional[str] = None


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    """Change password request for authenticated users"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class UserProfile(BaseModel):
    """User profile information"""
    user_id: str
    email: str
    first_name: str
    last_name: str
    role: str
    tenant_id: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True


class TenantInfo(BaseModel):
    """Tenant information"""
    tenant_id: str
    tenant_name: str
    plan: str
    features: List[str]
    created_at: datetime
    user_count: int
    rate_limits: Dict[str, int]


class TokenPayload(BaseModel):
    """JWT token payload structure"""
    sub: str  # user_id
    tenant_id: str
    role: str
    token_type: str
    iat: datetime
    exp: datetime
    nbf: datetime
    additional_claims: Optional[Dict[str, Any]] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda v: int(v.timestamp())
        }


class APIKeyRequest(BaseModel):
    """API key generation request"""
    name: str = Field(..., min_length=1, max_length=100)
    permissions: List[str] = []
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    """API key response"""
    key_id: str
    api_key: str  # Only returned once
    name: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime]


class RateLimitInfo(BaseModel):
    """Rate limit information"""
    limit: int
    remaining: int
    reset_at: datetime
    window_seconds: int