from fastapi import Request, HTTPException, status

async def get_current_user(request: Request) -> dict:
    '''
    Extract current user from request state (injected by JWT middleware).
    
    Raises:
        HTTPException: If user is not authenticated
        
    Returns:
        dict: User context with user_id, tenant_id, role, etc.
    '''
    if not hasattr(request.state, 'is_authenticated') or not request.state.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not hasattr(request.state, 'current_user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User context not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Return user context - already a dict from JWT middleware
    user_context = request.state.current_user
    
    # FIXED: Handle both dict and object formats
    if isinstance(user_context, dict):
        return user_context
    else:
        # If it's an object, convert to dict
        return {
            'user_id': str(getattr(user_context, 'user_id', '')),
            'email': getattr(user_context, 'email', ''),
            'tenant_id': str(getattr(user_context, 'tenant_id', '')),
            'role': getattr(user_context, 'role', ''),
            'is_active': getattr(user_context, 'is_active', True)
        }


async def get_optional_current_user(request: Request) -> dict:
    '''
    Extract current user from request state if available.
    Returns a stub dict when not authenticated (for public endpoints).
    '''
    if not hasattr(request.state, 'is_authenticated') or not request.state.is_authenticated:
        return {
            'user_id': 'anonymous',
            'email': 'anonymous',
            'tenant_id': None,
            'role': 'anonymous',
            'is_active': True,
        }

    if not hasattr(request.state, 'current_user'):
        return {
            'user_id': 'anonymous',
            'email': 'anonymous',
            'tenant_id': None,
            'role': 'anonymous',
            'is_active': True,
        }

    user_context = request.state.current_user
    if isinstance(user_context, dict):
        return user_context
    else:
        return {
            'user_id': str(getattr(user_context, 'user_id', '')),
            'email': getattr(user_context, 'email', ''),
            'tenant_id': str(getattr(user_context, 'tenant_id', '')),
            'role': getattr(user_context, 'role', ''),
            'is_active': getattr(user_context, 'is_active', True)
        }
