"""
JWT Authentication Usage Examples

This file demonstrates how to use the JWT authentication system
in your FastAPI routes and services.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.dependencies.auth import (
    RequireAuth, RequireTenant, RequireAdmin, 
    get_current_user, get_current_tenant,
    RoleRequired, PermissionRequired
)
from app.schemas.auth import UserContext, TenantContext, TokenResponse
from app.core.auth import jwt_handler


router = APIRouter()


# Example 1: Basic authentication required
@router.get("/protected-endpoint")
async def protected_endpoint(current_user: UserContext = RequireAuth):
    """Example endpoint requiring authentication"""
    return {
        "message": "This is a protected endpoint",
        "user_id": current_user.user_id,
        "tenant_id": current_user.tenant_id,
        "role": current_user.role
    }


# Example 2: Admin only endpoint
@router.get("/admin-only")
async def admin_only_endpoint(current_user: UserContext = RequireAdmin):
    """Example endpoint requiring admin role"""
    return {
        "message": "Admin access granted",
        "user": current_user.user_id
    }


# Example 3: Role-based access
@router.get("/manager-endpoint")
async def manager_endpoint(
    current_user: UserContext = Depends(RoleRequired(['manager', 'admin']))
):
    """Example endpoint for managers and admins"""
    return {
        "message": f"Manager access granted to {current_user.role}",
        "user": current_user.user_id
    }


# Example 4: Permission-based access
@router.get("/analytics-endpoint")
async def analytics_endpoint(
    current_user: UserContext = Depends(
        PermissionRequired(['view_analytics', 'access_reports'])
    )
):
    """Example endpoint requiring specific permissions"""
    return {
        "message": "Analytics access granted",
        "permissions": current_user.permissions
    }


# Example 5: Tenant context usage
@router.get("/tenant-data")
async def get_tenant_data(
    current_user: UserContext = RequireAuth,
    current_tenant: TenantContext = RequireTenant
):
    """Example endpoint using tenant context"""
    return {
        "tenant_id": current_tenant.tenant_id,
        "tenant_plan": current_tenant.plan,
        "user_count": len([]),  # Would query database
        "features": current_tenant.features
    }


# Example 6: Optional authentication
@router.get("/public-endpoint")
async def public_endpoint(
    current_user: UserContext = Depends(get_current_user_optional)
):
    """Example endpoint with optional authentication"""
    if current_user:
        return {
            "message": f"Hello authenticated user {current_user.user_id}",
            "authenticated": True
        }
    else:
        return {
            "message": "Hello anonymous user", 
            "authenticated": False
        }


# Example 7: Login endpoint (creates tokens)
@router.post("/auth/login")
async def login(email: str, password: str):
    """Example login endpoint"""
    
    # TODO: Verify credentials against database
    # user = authenticate_user(email, password)
    # if not user:
    #     raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Mock user data for example
    user_id = "user123"
    tenant_id = "tenant456" 
    role = "user"
    
    # Create tokens
    access_token = jwt_handler.create_access_token(
        user_id=user_id,
        tenant_id=tenant_id, 
        role=role
    )
    
    refresh_token = jwt_handler.create_refresh_token(
        user_id=user_id,
        tenant_id=tenant_id
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=1800,  # 30 minutes
        refresh_token=refresh_token,
        user_id=user_id,
        tenant_id=tenant_id,
        role=role
    )


# Example 8: Token refresh endpoint
@router.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    """Example token refresh endpoint"""
    try:
        # Decode refresh token
        payload = jwt_handler.decode_token(refresh_token)
        
        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=400,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        
        # TODO: Verify user still exists and is active
        
        # Create new access token
        new_access_token = jwt_handler.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            role="user"  # TODO: Get from database
        )
        
        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer", 
            expires_in=1800,
            user_id=user_id,
            tenant_id=tenant_id,
            role="user"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )


# Example 9: Logout endpoint (blacklist token)
@router.post("/auth/logout")
async def logout(current_user: UserContext = RequireAuth):
    """Example logout endpoint"""
    
    # TODO: Implement token blacklisting
    # blacklist_token(current_user.token)
    
    return {"message": "Successfully logged out"}


# Example 10: User profile endpoint
@router.get("/profile")
async def get_profile(current_user: UserContext = RequireAuth):
    """Get current user profile"""
    return {
        "user_id": current_user.user_id,
        "tenant_id": current_user.tenant_id,
        "role": current_user.role,
        "permissions": current_user.permissions,
        "token_claims": current_user.token_payload
    }
