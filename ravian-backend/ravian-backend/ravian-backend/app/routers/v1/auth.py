"""
Authentication Router

Handles user authentication endpoints:
- Registration
- Login
- Token refresh
- Logout
- Password reset
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict

from app.core.database import get_db_session
from app.core.auth import jwt_handler, hash_password, verify_password
from app.core.utils import get_tenant_id, get_user_id
from app.dependencies.auth import get_current_user
from app.models import User, Tenant
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserProfile
)

router = APIRouter()


@router.post('/auth/register', response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db_session)
) -> UserProfile:
    """Register a new user"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Handle tenant - create if doesn't exist or use existing
    tenant_name = request.tenant_name or "Default Organization"
    tenant = db.query(Tenant).filter(Tenant.name == tenant_name).first()
    
    if not tenant:
        # Create new tenant with required domain field
        domain = f"{tenant_name.lower().replace(' ', '-')}.ravian.com"
        tenant = Tenant(
            name=tenant_name,
            domain=domain
        )
        db.add(tenant)
        db.flush()  # Flush to get the tenant ID before creating user
    
    # Create new user
    new_user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        role=request.role,
        tenant_id=tenant.id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserProfile(
        user_id=str(new_user.id),
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        role=new_user.role.value,  # Convert enum to string
        tenant_id=str(new_user.tenant_id),
        created_at=new_user.created_at,
        is_active=bool(new_user.is_active)  # Fixed: Boolean field
    )


@router.post('/auth/login')
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db_session)
) -> Dict:
    """Login and get access token"""
    
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:  # Fixed: Boolean field
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Generate tokens
    access_token = jwt_handler.create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role.value  # FIXED: Convert enum to string
    )
    
    refresh_token = jwt_handler.create_refresh_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "user_id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "tenant_id": str(user.tenant_id),
            "role": user.role.value,
        },
    }


@router.post('/auth/refresh', response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db_session)
) -> TokenResponse:
    """Refresh access token using refresh token"""
    
    try:
        # Decode refresh token
        payload = jwt_handler.decode_token(refresh_token)
        
        if payload.get('token_type') != 'refresh':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get('sub')
        tenant_id = payload.get('tenant_id')
        
        # Verify user still exists and is active
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:  # Fixed: Boolean field
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new access token
        access_token = jwt_handler.create_access_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role.value  # FIXED: Convert enum to string
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600,
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role.value  # FIXED: Convert enum to string
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


@router.post('/auth/logout')
async def logout() -> Dict[str, str]:
    """Logout user (client should delete tokens)"""
    return {"message": "Successfully logged out"}


@router.get("/auth/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get current authenticated user information"""
    user_id = current_user["user_id"]
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get tenant name for display
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    
    return {
        "user_id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role.value if user.role else "VIEWER",
        "tenant_id": str(user.tenant_id),
        "tenant_name": tenant.name if tenant else None,
        "is_active": bool(user.is_active),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }