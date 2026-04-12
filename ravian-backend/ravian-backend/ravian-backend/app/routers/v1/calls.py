"""
Call management API endpoints for CRM system.
Handles call logging, AI call triggering, and call analytics.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
import logging
import redis

# CORRECTED IMPORTS for your backend structure
from app.core.database import get_db_session
from app.core.redis_client import get_redis_client
from app.core.utils import get_tenant_id, get_user_id
from app.dependencies.auth import get_current_user

# Import schemas
from app.schemas.call import (
    CallLogCreate,
    CallLogResponse,
    TriggerCallRequest
)

# Import service
from app.services.call_service import CallService

# Configure logging
logger = logging.getLogger(__name__)

# Create router (prefix matches leads pattern so /api/v1/calls/ works when mounted at /api/v1)
router = APIRouter(prefix="/calls")


def increment_usage_counter(redis_client: redis.Redis, tenant_id: UUID, counter_type: str = "calls"):
    """Increment usage counter in Redis with 90-day expiry"""
    try:
        current_month = datetime.now().strftime("%Y-%m")
        key = f"usage:{tenant_id}:{counter_type}:{current_month}"
        redis_client.incr(key)
        redis_client.expire(key, 90 * 24 * 60 * 60)  # 90 days
        logger.info(f"Incremented usage counter: {key}")
    except Exception as e:
        logger.warning(f"Failed to increment usage counter for tenant {tenant_id}: {str(e)}")


@router.post("/", response_model=CallLogResponse, status_code=status.HTTP_201_CREATED)
async def create_call_log(
    call_data: CallLogCreate,
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new call log (manual or from voice agent)
    
    Features:
    - Validates lead exists and belongs to tenant
    - Calculates cost based on duration
    - Analyzes sentiment from transcript
    - Logs analytics event
    """
    try:
        tenant_id = get_tenant_id(current_user)
        user_id = UUID(current_user.get("user_id"))
        
        logger.info(f"Creating call log for tenant {tenant_id}, user {user_id}")
        
        # Initialize call service
        call_service = CallService(db=db, redis_client=redis_client, tenant_id=tenant_id)
        
        # Create call log
        call_response = call_service.create_call_log(call_data=call_data, user_id=user_id)
        
        # Increment usage counter
        increment_usage_counter(redis_client, tenant_id, "calls")
        
        logger.info(f"Call log created successfully: {call_response.id}")
        return call_response
        
    except Exception as e:
        logger.error(f"Error creating call log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create call log"
        )


@router.get("/", response_model=Dict[str, Any])
async def list_calls(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    outcome: Optional[str] = Query(None, description="Filter by call outcome"),
    call_direction: Optional[str] = Query(None, description="Filter by call direction"),
    lead_id: Optional[UUID] = Query(None, description="Filter by lead ID"),
    created_after: Optional[datetime] = Query(None, description="Filter calls from datetime"),
    created_before: Optional[datetime] = Query(None, description="Filter calls to datetime"),
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List calls with filters and pagination
    
    Supports filters: sentiment, outcome, direction, lead_id, date range
    Returns paginated results with total count
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Listing calls for tenant {tenant_id}, page {page}")
        
        # Initialize call service
        call_service = CallService(db=db, redis_client=redis_client, tenant_id=tenant_id)
        
        # Get calls with pagination
        calls, total_count = call_service.get_calls(
            sentiment=sentiment,
            outcome=outcome,
            call_direction=call_direction,
            lead_id=lead_id,
            created_after=created_after,
            created_before=created_before,
            page=page,
            limit=limit
        )
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        
        response = {
            "calls": calls,
            "total": total_count,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
                "page_size": limit,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "filters_applied": {
                "sentiment": sentiment,
                "outcome": outcome,
                "call_direction": call_direction,
                "lead_id": str(lead_id) if lead_id else None,
                "created_after": str(created_after) if created_after else None,
                "created_before": str(created_before) if created_before else None
            }
        }
        
        logger.info(f"Retrieved {len(calls)} calls for tenant {tenant_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error listing calls: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve calls"
        )


@router.get("/{call_id}", response_model=Dict[str, Any])
async def get_call_details(
    call_id: UUID = Path(..., description="Call ID"),
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get call details by ID
    
    Returns complete call information including lead data
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Retrieving call {call_id} for tenant {tenant_id}")
        
        # Initialize call service
        call_service = CallService(db=db, redis_client=redis_client, tenant_id=tenant_id)
        
        # Get call by ID
        call_response = call_service.get_call_by_id(call_id)
        
        logger.info(f"Call {call_id} retrieved successfully")
        return call_response
        
    except Exception as e:
        logger.error(f"Error retrieving call {call_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call {call_id} not found"
        )


@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call(
    call_id: UUID = Path(..., description="Call ID"),
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Soft-delete a call log (sets is_deleted=True)."""
    try:
        from app.models.call import CallLog
        from app.models.lead import Lead
        tenant_id = get_tenant_id(current_user)
        call = db.query(CallLog).join(Lead).filter(
            CallLog.id == call_id,
            Lead.tenant_id == tenant_id
        ).first()
        if not call:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )
        call.is_deleted = True
        db.commit()
        logger.info(f"Call {call_id} soft-deleted for tenant {tenant_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting call {call_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete call"
        )


@router.patch("/{call_id}", response_model=Dict[str, Any])
async def update_call(
    call_id: UUID = Path(..., description="Call ID"),
    transcript: Optional[str] = None,
    summary: Optional[str] = None,
    sentiment: Optional[str] = None,
    outcome: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update call details
    
    Can update: transcript, summary, sentiment, outcome, notes
    Re-analyzes sentiment if transcript is updated
    """
    try:
        tenant_id = get_tenant_id(current_user)
        user_id = UUID(current_user.get("user_id"))
        
        logger.info(f"Updating call {call_id} for tenant {tenant_id}")
        
        # Initialize call service
        call_service = CallService(db=db, redis_client=redis_client, tenant_id=tenant_id)
        
        # Update call
        call_response = call_service.update_call(
            call_id=call_id,
            transcript=transcript,
            summary=summary,
            sentiment=sentiment,
            outcome=outcome,
            notes=notes,
            user_id=user_id
        )
        
        logger.info(f"Call {call_id} updated successfully")
        return call_response
        
    except Exception as e:
        logger.error(f"Error updating call {call_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update call"
        )


@router.post("/trigger", response_model=Dict[str, Any])
async def trigger_outbound_call(
    trigger_request: TriggerCallRequest,
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Trigger outbound call (queues for voice agent)
    
    Features:
    - Validates lead exists
    - Adds to Redis queue based on priority
    - Creates call log with "queued" status
    - Returns queue position and estimated wait time
    """
    try:
        tenant_id = get_tenant_id(current_user)
        user_id = UUID(current_user.get("user_id"))
        
        logger.info(f"Triggering outbound call for lead {trigger_request.lead_id}")
        
        # Initialize call service
        call_service = CallService(db=db, redis_client=redis_client, tenant_id=tenant_id)
        
        # Trigger call
        result = call_service.trigger_outbound_call(
            request=trigger_request,
            user_id=user_id
        )
        
        # Increment usage counter
        increment_usage_counter(redis_client, tenant_id, "outbound_calls")
        
        logger.info(f"Outbound call triggered successfully")
        
        return {
            "success": True,
            "message": "Outbound call queued successfully",
            **result
        }
        
    except Exception as e:
        logger.error(f"Error triggering call: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger outbound call"
        )


@router.get("/{call_id}/transcript", response_model=Dict[str, Any])
async def get_call_transcript(
    call_id: UUID = Path(..., description="Call ID"),
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get call transcript with sentiment
    
    Returns transcript text and sentiment analysis
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Retrieving transcript for call {call_id}")
        
        # Initialize call service
        call_service = CallService(db=db, redis_client=redis_client, tenant_id=tenant_id)
        
        # Get call
        call_response = call_service.get_call_by_id(call_id)
        
        if not call_response.get("transcript"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not available for this call"
            )
        
        response = {
            "transcript": call_response.get("transcript"),
            "sentiment": call_response.get("sentiment", "neutral"),
            "call_id": call_id
        }
        
        logger.info(f"Transcript retrieved for call {call_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transcript: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transcript"
        )


@router.post("/{call_id}/analyze", response_model=Dict[str, Any])
async def analyze_call_sentiment(
    call_id: UUID = Path(..., description="Call ID"),
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Run sentiment/intent analysis on transcript
    
    Uses keyword-based sentiment analysis
    Returns sentiment, confidence, and keywords
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Analyzing sentiment for call {call_id}")
        
        # Initialize call service
        call_service = CallService(db=db, redis_client=redis_client, tenant_id=tenant_id)
        
        # Get call
        call_response = call_service.get_call_by_id(call_id)
        
        if not call_response.get("transcript"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transcript available for analysis"
            )
        
        # Analyze sentiment
        sentiment = call_service.analyze_sentiment(call_response.get("transcript"))
        
        # Increment usage counter
        increment_usage_counter(redis_client, tenant_id, "ai_analysis")
        
        response = {
            "sentiment": sentiment,
            "confidence": 0.85,  # Mock confidence
            "keywords": []  # Could extract keywords if needed
        }
        
        logger.info(f"Sentiment analysis completed: {sentiment}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze sentiment"
        )