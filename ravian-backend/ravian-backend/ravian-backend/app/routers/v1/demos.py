"""
Demo management API endpoints for CRM system.
Handles demo scheduling, availability checking, and outcome tracking.
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
from app.schemas.demo import (
    DemoCreate,
    DemoUpdate,
    DemoResponse
)

# Import service
from app.services.demo_service import (
    DemoService,
    DemoNotFoundError,
    LeadNotFoundError,
    MentorNotFoundError,
    SlotNotAvailableError,
    RescheduleLimitExceededError
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router (prefix matches leads pattern so /api/v1/demos/ works when mounted at /api/v1)
router = APIRouter(prefix="/demos")


@router.get("/available-slots", response_model=List[datetime])
async def get_available_slots(
    target_date: date = Query(..., description="Date to check availability"),
    mentor_id: Optional[UUID] = Query(None, description="Optional specific mentor"),
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get available 30-minute demo slots for a given date
    
    Features:
    - Slots from 10 AM to 8 PM
    - Excludes already booked slots
    - Optional filter by specific mentor
    
    Returns:
        List of available datetime slots
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Getting available slots for date {target_date}, mentor {mentor_id}")
        
        # Initialize demo service
        demo_service = DemoService(db=db, tenant_id=tenant_id)
        
        # Get available slots
        available_slots = demo_service.get_available_slots(
            target_date=target_date,
            mentor_id=mentor_id
        )
        
        logger.info(f"Found {len(available_slots)} available slots")
        return available_slots
        
    except MentorNotFoundError as e:
        logger.error(f"Mentor not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Error getting available slots: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available slots"
        )


@router.post("/", response_model=DemoResponse, status_code=status.HTTP_201_CREATED)
async def schedule_demo(
    demo_data: DemoCreate,
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Schedule a new demo
    
    Features:
    - Validates lead and course exist
    - Checks slot availability
    - Auto-assigns mentor if not provided
    - Queues reminder in Redis (1 hour before)
    - Updates lead status to 'demo_scheduled'
    - Logs analytics event
    
    Returns:
        Created demo with nested lead, mentor, course data
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Scheduling demo for lead {demo_data.lead_id}")
        
        # Initialize demo service
        demo_service = DemoService(db=db, tenant_id=tenant_id)
        
        # Schedule demo
        demo_response = demo_service.schedule_demo(demo_data=demo_data)
        
        logger.info(f"Demo scheduled successfully: {demo_response.id}")
        return demo_response
        
    except LeadNotFoundError as e:
        logger.error(f"Lead not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except MentorNotFoundError as e:
        logger.error(f"Mentor not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except SlotNotAvailableError as e:
        logger.error(f"Slot not available: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error scheduling demo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule demo"
        )


@router.get("/", response_model=Dict[str, Any])
async def list_demos(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    date_from: Optional[datetime] = Query(None, description="Filter demos from date"),
    date_to: Optional[datetime] = Query(None, description="Filter demos to date"),
    status: Optional[str] = Query(None, description="Filter by status (scheduled, completed, no_show, cancelled)"),
    mentor_id: Optional[UUID] = Query(None, description="Filter by mentor"),
    lead_id: Optional[UUID] = Query(None, description="Filter by lead"),
    search: Optional[str] = Query(None, description="Search in lead name, email, notes"),
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List demos with filters and pagination
    
    Supports filters: date range, status, mentor, lead, search
    Returns paginated results with total count
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Listing demos for tenant {tenant_id}, page {page}")
        
        # Initialize demo service
        demo_service = DemoService(db=db, tenant_id=tenant_id)
        
        # Build filters
        filters = {}
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        if status:
            filters["status"] = status
        if mentor_id:
            filters["mentor_id"] = mentor_id
        if lead_id:
            filters["lead_id"] = lead_id
        if search:
            filters["search"] = search
        
        # Get demos
        demos, total_count = demo_service.get_demos(
            filters=filters,
            page=page,
            per_page=per_page
        )
        
        # Enrich demos with lead names
        from app.models.lead import Lead
        enriched_demos = []
        for demo in demos:
            demo_dict = demo.dict() if hasattr(demo, 'dict') else demo
            if isinstance(demo_dict, dict) and demo_dict.get('lead_id'):
                lead = db.query(Lead).filter(Lead.id == demo_dict['lead_id']).first()
                demo_dict['lead_name'] = lead.name if lead and lead.name else (lead.email if lead else f"Lead {str(demo_dict['lead_id'])[:8]}")
            enriched_demos.append(demo_dict)
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        
        response = {
            "demos": enriched_demos,
            "total": total_count,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
                "page_size": per_page,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "filters_applied": {
                "date_from": str(date_from) if date_from else None,
                "date_to": str(date_to) if date_to else None,
                "status": status,
                "mentor_id": str(mentor_id) if mentor_id else None,
                "lead_id": str(lead_id) if lead_id else None,
                "search": search
            }
        }
        
        logger.info(f"Retrieved {len(demos)} demos for tenant {tenant_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error listing demos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve demos"
        )


@router.get("/{demo_id}", response_model=DemoResponse)
async def get_demo_details(
    demo_id: UUID = Path(..., description="Demo ID"),
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get demo details by ID
    
    Returns complete demo information with nested lead, mentor, course data
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Retrieving demo {demo_id} for tenant {tenant_id}")
        
        # Initialize demo service
        demo_service = DemoService(db=db, tenant_id=tenant_id)
        
        # Get demo by ID
        demo_response = demo_service.get_demo_by_id(demo_id)
        
        logger.info(f"Demo {demo_id} retrieved successfully")
        return demo_response
        
    except DemoNotFoundError as e:
        logger.error(f"Demo not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving demo {demo_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve demo"
        )


@router.patch("/{demo_id}", response_model=DemoResponse)
async def update_demo(
    demo_id: UUID = Path(..., description="Demo ID"),
    update_data: DemoUpdate = ...,
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update demo details
    
    Features:
    - Reschedule with availability check (max 2 reschedules)
    - Mark attendance
    - Set outcome (no_show, completed, rescheduled, cancelled)
    - Updates lead status based on outcome
    - Queues new reminder if rescheduled
    
    Returns:
        Updated demo
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Updating demo {demo_id} for tenant {tenant_id}")
        
        # Initialize demo service
        demo_service = DemoService(db=db, tenant_id=tenant_id)
        
        # Update demo
        demo_response = demo_service.update_demo(
            demo_id=demo_id,
            update_data=update_data
        )
        
        logger.info(f"Demo {demo_id} updated successfully")
        return demo_response
        
    except DemoNotFoundError as e:
        logger.error(f"Demo not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RescheduleLimitExceededError as e:
        logger.error(f"Reschedule limit exceeded: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except SlotNotAvailableError as e:
        logger.error(f"Slot not available: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating demo {demo_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update demo"
        )


@router.delete("/{demo_id}", response_model=DemoResponse)
async def cancel_demo(
    demo_id: UUID = Path(..., description="Demo ID"),
    reason: str = Query("Cancelled by user", description="Cancellation reason"),
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cancel a demo
    
    Features:
    - Sets outcome to 'cancelled'
    - Updates lead status to 'nurture'
    - Logs cancellation reason
    - Logs analytics event
    
    Returns:
        Cancelled demo
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Cancelling demo {demo_id} for tenant {tenant_id}")
        
        # Initialize demo service
        demo_service = DemoService(db=db, tenant_id=tenant_id)
        
        # Cancel demo
        demo_response = demo_service.cancel_demo(
            demo_id=demo_id,
            reason=reason
        )
        
        logger.info(f"Demo {demo_id} cancelled successfully")
        return demo_response
        
    except DemoNotFoundError as e:
        logger.error(f"Demo not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error cancelling demo {demo_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel demo"
        )


@router.post("/{demo_id}/reminder", response_model=Dict[str, Any])
async def send_demo_reminder(
    demo_id: UUID = Path(..., description="Demo ID"),
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Send demo reminder manually
    
    Triggers reminder notification for the demo
    (Placeholder for SMS/Email integration)
    
    Returns:
        Reminder status
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Sending reminder for demo {demo_id}")
        
        # Initialize demo service
        demo_service = DemoService(db=db, tenant_id=tenant_id)
        
        # Send reminder
        result = demo_service.send_reminder(demo_id=demo_id)
        
        logger.info(f"Reminder sent for demo {demo_id}")
        return result
        
    except DemoNotFoundError as e:
        logger.error(f"Demo not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error sending reminder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reminder"
        )


@router.post("/check-no-shows", response_model=Dict[str, Any])
async def check_no_shows(
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Check for no-show demos and mark them
    
    Features:
    - Finds demos scheduled >1 hour ago with no attendance record
    - Marks as 'no_show'
    - Updates lead status to 'nurture'
    - Logs analytics events
    
    Returns:
        List of demo IDs marked as no-show
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Checking for no-shows for tenant {tenant_id}")
        
        # Initialize demo service
        demo_service = DemoService(db=db, tenant_id=tenant_id)
        
        # Check no-shows
        no_show_ids = demo_service.check_no_shows()
        
        logger.info(f"Marked {len(no_show_ids)} demos as no-show")
        
        return {
            "no_show_count": len(no_show_ids),
            "demo_ids": [str(demo_id) for demo_id in no_show_ids],
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking no-shows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check no-shows"
        )