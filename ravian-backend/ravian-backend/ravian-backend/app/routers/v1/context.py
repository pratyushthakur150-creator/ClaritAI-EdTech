from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

# Database and authentication dependencies
from app.core.database import get_db_session
from app.dependencies.auth import get_current_user
from app.schemas.context import (
    ContextCreateRequest,
    ContextResponse,
    AddMessageRequest,
    ContextStatsResponse
)
from app.services.context_service import ContextService

# Create router
router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_context(
    request: ContextCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Create a new conversation context.
    
    Creates a new conversation context for a user with optional initial messages.
    Supports different context types: chatbot, voice_agent, teaching_assistant.
    
    Args:
        request: Context creation request containing user_id, context_type, 
                initial_messages, and optional metadata
        current_user: Authenticated user information from JWT token
        db: Database session
        
    Returns:
        ContextResponse: Complete context details including messages and metadata
        
    Raises:
        HTTPException 400: Invalid context_type or too many initial messages
        HTTPException 500: Server error during context creation
    """
    try:
        print(f"Creating new context for user {getattr(request, 'user_id', 'unknown')}, type: {getattr(request, 'context_type', 'unknown')}")
        
        # Extract tenant_id from authenticated user
        tenant_id = current_user["tenant_id"]
        
        # Initialize service
        context_service = ContextService(db)
        
        # Convert initial messages to dict format if provided
        initial_messages = None
        if hasattr(request, 'initial_messages') and request.initial_messages:
            initial_messages = [
                {
                    "role": getattr(msg, 'role', 'user'),
                    "content": getattr(msg, 'content', ''),
                    "metadata": getattr(msg, 'metadata', {}) or {}
                }
                for msg in request.initial_messages
            ]
        
        # Create context through service
        context = await context_service.create_context(
            user_id=str(getattr(request, 'user_id', "00000000-0000-0000-0000-000000000000")),
            context_type=getattr(request, 'context_type', 'chatbot'),
            tenant_id=tenant_id,
            initial_messages=initial_messages,
            metadata=getattr(request, 'metadata', {})
        )
        
        print(f"[OK] Context created successfully: {context.get('context_id', 'unknown')}")
        return context
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[FAIL] Error creating context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create context: {str(e)}"
        )

@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def add_message(
    request: AddMessageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Add a message to an existing conversation context.
    
    Adds a new message to the specified context. Automatically trims context
    if it exceeds maximum length. Updates context timestamp.
    
    Args:
        request: Message addition request containing context_id, role, 
                content, and optional metadata
        current_user: Authenticated user information from JWT token
        db: Database session
        
    Returns:
        Dict: Success response with message details and updated context info
        
    Raises:
        HTTPException 400: Invalid role, empty content, or content too long
        HTTPException 404: Context not found or access denied
        HTTPException 500: Server error during message addition
    """
    try:
        print(f"Adding message to context {getattr(request, 'context_id', 'unknown')}, role: {getattr(request, 'role', 'unknown')}")
        
        # Extract tenant_id from authenticated user
        tenant_id = current_user["tenant_id"]
        
        # Initialize service
        context_service = ContextService(db)
        
        # Add message through service
        result = await context_service.add_message(
            context_id=str(getattr(request, 'context_id', "00000000-0000-0000-0000-000000000000")),
            role=getattr(request, 'role', 'user'),
            content=getattr(request, 'content', ''),
            tenant_id=tenant_id,
            metadata=getattr(request, 'metadata', {})
        )
        
        print(f"[OK] Message added successfully to context {getattr(request, 'context_id', 'unknown')}")
        return {
            "success": True,
            "message": "Message added successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[FAIL] Error adding message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )

@router.get("/{context_id}")
async def get_context(
    context_id: UUID = Path(..., description="UUID of the conversation context"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve complete conversation context details.
    
    Returns full context information including all messages, metadata,
    message count, and timestamps. Filtered by tenant for security.
    
    Args:
        context_id: UUID of the context to retrieve
        current_user: Authenticated user information from JWT token
        db: Database session
        
    Returns:
        ContextResponse: Complete context details with all messages
        
    Raises:
        HTTPException 404: Context not found or access denied
        HTTPException 500: Server error during context retrieval
    """
    try:
        print(f"Retrieving context details for {context_id}")
        
        # Extract tenant_id from authenticated user
        tenant_id = current_user["tenant_id"]
        
        # Initialize service
        context_service = ContextService(db)
        
        # Retrieve context through service
        context = await context_service.get_context(
            context_id=str(context_id),
            tenant_id=tenant_id
        )
        
        print(f"[OK] Context details retrieved for {context_id}")
        return context
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[FAIL] Error retrieving context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve context: {str(e)}"
        )

@router.delete("/{context_id}")
async def delete_context(
    context_id: UUID = Path(..., description="UUID of the conversation context"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Delete a conversation context and all its messages.
    
    Permanently removes the context and all associated messages from the system.
    This operation cannot be undone. Filtered by tenant for security.
    
    Args:
        context_id: UUID of the context to delete
        current_user: Authenticated user information from JWT token
        db: Database session
        
    Returns:
        Dict: Deletion confirmation with timestamp and message count
        
    Raises:
        HTTPException 404: Context not found or access denied
        HTTPException 500: Server error during context deletion
    """
    try:
        print(f"Deleting context {context_id}")
        
        # Extract tenant_id from authenticated user
        tenant_id = current_user["tenant_id"]
        
        # Initialize service
        context_service = ContextService(db)
        
        # Delete context through service
        result = await context_service.delete_context(
            context_id=str(context_id),
            tenant_id=tenant_id
        )
        
        print(f"[OK] Context {context_id} deleted successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[FAIL] Error deleting context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete context: {str(e)}"
        )

@router.get("/users/{user_id}")
async def get_user_contexts(
    user_id: UUID = Path(..., description="UUID of the user"),
    context_type: Optional[str] = Query(None, description="Filter by context type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of contexts to return"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve all contexts for a specific user.
    
    Returns a list of contexts belonging to the specified user, with optional
    filtering by context type. Results are ordered by last update time.
    
    Args:
        user_id: UUID of the user whose contexts to retrieve
        context_type: Optional filter by context type (chatbot, voice_agent, teaching_assistant)
        limit: Maximum number of contexts to return (1-200, default 50)
        current_user: Authenticated user information from JWT token
        db: Database session
        
    Returns:
        Dict: List of user contexts with metadata and pagination info
        
    Raises:
        HTTPException 400: Invalid context_type filter
        HTTPException 500: Server error during context retrieval
    """
    try:
        print(f"Retrieving contexts for user {user_id}")
        
        # Extract tenant_id from authenticated user
        tenant_id = current_user["tenant_id"]
        
        # Validate context_type filter if provided
        if context_type:
            valid_types = ["chatbot", "voice_agent", "teaching_assistant"]
            if context_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid context_type. Must be one of: {', '.join(valid_types)}"
                )
        
        # Initialize service
        context_service = ContextService(db)
        
        # Retrieve user contexts through service
        result = await context_service.get_user_contexts(
            user_id=str(user_id),
            tenant_id=tenant_id,
            context_type=context_type,
            limit=limit
        )
        
        print(f"[OK] Retrieved {result.get('total_count', 0)} contexts for user {user_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[FAIL] Error retrieving user contexts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user contexts: {str(e)}"
        )

@router.get("/stats/overview")
async def get_context_stats(
    date_from: Optional[datetime] = Query(None, description="Start date for statistics"),
    date_to: Optional[datetime] = Query(None, description="End date for statistics"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get conversation context usage statistics.
    
    Returns comprehensive statistics about context usage including total contexts,
    messages, breakdowns by type and role, active contexts, and averages.
    Defaults to last 30 days if no date range provided.
    
    Args:
        date_from: Start date for statistics (defaults to 30 days ago)
        date_to: End date for statistics (defaults to now)
        current_user: Authenticated user information from JWT token
        db: Database session
        
    Returns:
        ContextStatsResponse: Complete usage statistics with breakdowns and metrics
        
    Raises:
        HTTPException 400: Invalid date range (date_from > date_to)
        HTTPException 500: Server error during statistics calculation
    """
    try:
        print("Fetching context usage statistics")
        
        # Extract tenant_id from authenticated user
        tenant_id = current_user["tenant_id"]
        
        # Set default date range if not provided (last 30 days)
        now = datetime.utcnow()
        if not date_from:
            date_from = now - timedelta(days=30)
        if not date_to:
            date_to = now
        
        # Validate date range
        if date_from > date_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="date_from cannot be later than date_to"
            )
        
        # Initialize service
        context_service = ContextService(db)
        
        # Get statistics through service
        stats = await context_service.get_context_stats(
            tenant_id=tenant_id,
            date_from=date_from,
            date_to=date_to
        )
        
        print(f"[OK] Context statistics retrieved for period {date_from} to {date_to}")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[FAIL] Error fetching context stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch context stats: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for conversation context service.
    
    Simple health check to verify the context service is operational.
    Does not require authentication for monitoring purposes.
    
    Returns:
        Dict: Health status information
    """
    try:
        print("Context service health check requested")
        
        health_status = {
            "service": "conversation-context",
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "version": "1.0.0",
            "features": [
                "context_creation",
                "message_handling",
                "context_retrieval",
                "usage_statistics",
                "context_trimming",
                "multi_tenant_support"
            ]
        }
        
        print("[OK] Context service health check completed")
        return health_status
        
    except Exception as e:
        print(f"[FAIL] Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )