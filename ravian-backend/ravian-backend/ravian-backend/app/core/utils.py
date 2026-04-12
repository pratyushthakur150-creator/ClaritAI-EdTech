"""
Utility functions for common operations across the application
"""
from typing import Union
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


def ensure_uuid(value: Union[str, UUID, None]) -> UUID:
    """
    Convert value to UUID, handling various input types.
    
    Args:
        value: String, UUID, or None
        
    Returns:
        UUID object
        
    Raises:
        ValueError: If value cannot be converted to UUID
    """
    if value is None:
        raise ValueError("Cannot convert None to UUID")
    
    if isinstance(value, UUID):
        return value
    
    if isinstance(value, str):
        try:
            return UUID(value)
        except ValueError as e:
            raise ValueError(f"Invalid UUID string: {value}") from e
    
    raise ValueError(f"Cannot convert {type(value)} to UUID")


def get_tenant_id(current_user: dict) -> UUID:
    """
    Extract and validate tenant_id from current_user context.
    
    Args:
        current_user: User context dictionary from JWT middleware
        
    Returns:
        UUID tenant_id
        
    Raises:
        ValueError: If tenant_id is missing or invalid
    """
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise ValueError("tenant_id not found in user context")
    
    return ensure_uuid(tenant_id)


def get_user_id(current_user: dict) -> UUID:
    """
    Extract and validate user_id from current_user context.
    
    Args:
        current_user: User context dictionary from JWT middleware
        
    Returns:
        UUID user_id
        
    Raises:
        ValueError: If user_id is missing or invalid
    """
    user_id = current_user.get("user_id")
    if not user_id:
        raise ValueError("user_id not found in user context")
    
    return ensure_uuid(user_id)
