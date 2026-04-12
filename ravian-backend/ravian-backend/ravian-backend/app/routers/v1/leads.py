"""
Lead management API endpoints for CRM system.
Provides comprehensive lead lifecycle management with multi-tenant security.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

try:
    import redis  # type: ignore
except ImportError:
    redis = None  # type: ignore

# CORRECTED IMPORTS for your backend structure
from app.core.database import get_db_session
from app.core.redis_client import get_redis_client
from app.core.utils import get_tenant_id, get_user_id
from app.dependencies.auth import get_current_user

# Import schemas
from app.schemas.lead import (
    LeadCreate, 
    LeadUpdate, 
    LeadResponse, 
    LeadTimeline
)

# Import service layer
from app.services.lead_service import LeadService, DuplicateLeadError, InvalidPhoneNumberError

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/leads")


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    db: Session = Depends(get_db_session),
    redis_client = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> LeadResponse:
    """
    Create a new lead from chatbot or manual input.
    
    - Validates phone number format
    - Handles duplicate detection with context merging
    - Auto-assigns to mentor via round-robin
    - Links chatbot session if sessionId provided
    - Logs analytics event and increments usage counter
    """
    try:
        tenant_id = get_tenant_id(current_user)
        user_id = get_user_id(current_user)
        
        logger.info(f"Creating lead for tenant {tenant_id}", 
                   extra={"tenant_id": str(tenant_id), "user_id": str(user_id)})
        
        # Initialize lead service
        lead_service = LeadService(db=db, redis_client=redis_client, current_user=current_user)
        
        # Create lead with business logic
        lead = lead_service.create_lead(lead_data=lead_data)
        
        # Increment usage counter in Redis
        try:
            redis_client.incr(f"tenant:{tenant_id}:leads_created")
            redis_client.incr(f"tenant:{tenant_id}:api_calls")
        except Exception as redis_error:
            logger.warning(f"Failed to increment Redis counters: {redis_error}")
        
        logger.info(f"Lead created successfully: {lead.id}", 
                   extra={"tenant_id": str(tenant_id), "lead_id": str(lead.id)})
        
        return lead
        
    except InvalidPhoneNumberError as e:
        logger.error(f"Invalid phone number: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DuplicateLeadError as e:
        logger.warning(f"Duplicate lead: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValueError as e:
        logger.error(f"Validation error creating lead: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create lead"
        )


@router.get("/", response_model=Dict[str, Any])
async def list_leads(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Max records"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    assigned_to: Optional[UUID] = Query(None, description="Filter by assigned user"),
    search: Optional[str] = Query(None, description="Search in name, email, phone"),
    db: Session = Depends(get_db_session),
    redis_client = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List leads with filtering and pagination.
    
    Supports filters: status, source, assigned_to, search
    Returns paginated results with total count and filter information
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Listing leads for tenant {tenant_id}", 
                   extra={"tenant_id": str(tenant_id), "skip": skip, "limit": limit})
        
        # Initialize lead service
        lead_service = LeadService(db=db, redis_client=redis_client, current_user=current_user)
        
        # Get leads with pagination
        leads, total_count = lead_service.get_leads(
            skip=skip,
            limit=limit,
            status=status_filter,
            source=source,
            assigned_to=assigned_to,
            search=search
        )
        
        # Calculate pagination info
        page = (skip // limit) + 1
        total_pages = (total_count + limit - 1) // limit
        
        # Increment usage counter
        try:
            redis_client.incr(f"tenant:{tenant_id}:api_calls")
        except Exception as redis_error:
            logger.warning(f"Failed to increment Redis counters: {redis_error}")
        
        response = {
            "leads": [lead.model_dump(mode="json", by_alias=True) for lead in leads],
            "total": total_count,
            "pagination": {
                "total": total_count,
                "page": page,
                "per_page": limit,
                "total_pages": total_pages,
                "has_next": skip + limit < total_count,
                "has_prev": skip > 0,
            },
            "filters_applied": {
                "status": status_filter,
                "source": source,
                "assigned_to": str(assigned_to) if assigned_to else None,
                "search": search,
            } if any([status_filter, source, assigned_to, search]) else None
        }
        
        logger.info(f"Retrieved {len(leads)} leads (total: {total_count})", 
                   extra={"tenant_id": str(tenant_id)})
        
        return response
        
    except Exception as e:
        import traceback
        logger.error(f"Error listing leads: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve leads: {str(e)}"
        )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    db: Session = Depends(get_db_session),
    redis_client = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> LeadResponse:
    """
    Get detailed information about a specific lead.
    
    Validates tenant access and returns complete lead data
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Retrieving lead {lead_id} for tenant {tenant_id}", 
                   extra={"tenant_id": str(tenant_id), "lead_id": str(lead_id)})
        
        # Initialize lead service
        lead_service = LeadService(db=db, redis_client=redis_client, current_user=current_user)
        
        # Get lead by ID
        lead = lead_service.get_lead_by_id(lead_id=lead_id)
        
        # Increment usage counter
        try:
            redis_client.incr(f"tenant:{tenant_id}:api_calls")
        except Exception as redis_error:
            logger.warning(f"Failed to increment Redis counters: {redis_error}")
        
        logger.info(f"Lead {lead_id} retrieved successfully", 
                   extra={"tenant_id": str(tenant_id), "lead_id": str(lead_id)})
        
        return lead
        
    except Exception as e:
        logger.error(f"Error retrieving lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} not found"
        )


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    lead_update: LeadUpdate,
    db: Session = Depends(get_db_session),
    redis_client = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> LeadResponse:
    """
    Update lead information (status, assignment, notes, etc.).
    
    Validates status transitions and tenant access
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Updating lead {lead_id} for tenant {tenant_id}", 
                   extra={"tenant_id": str(tenant_id), "lead_id": str(lead_id)})
        
        # Initialize lead service
        lead_service = LeadService(db=db, redis_client=redis_client, current_user=current_user)
        
        # Update lead
        lead = lead_service.update_lead(
            lead_id=lead_id,
            lead_data=lead_update
        )
        
        # Increment usage counter
        try:
            redis_client.incr(f"tenant:{tenant_id}:leads_updated")
            redis_client.incr(f"tenant:{tenant_id}:api_calls")
        except Exception as redis_error:
            logger.warning(f"Failed to increment Redis counters: {redis_error}")
        
        logger.info(f"Lead {lead_id} updated successfully", 
                   extra={"tenant_id": str(tenant_id), "lead_id": str(lead_id)})
        
        return lead
        
    except ValueError as e:
        logger.error(f"Validation error updating lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update lead"
        )


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: UUID,
    db: Session = Depends(get_db_session),
    redis_client = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Soft delete a lead (sets is_deleted flag).
    
    Validates tenant access before deletion
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Deleting lead {lead_id} for tenant {tenant_id}", 
                   extra={"tenant_id": str(tenant_id), "lead_id": str(lead_id)})
        
        # Initialize lead service
        lead_service = LeadService(db=db, redis_client=redis_client, current_user=current_user)
        
        # Delete lead
        success = lead_service.delete_lead(lead_id=lead_id)
        
        # Increment usage counter
        try:
            redis_client.incr(f"tenant:{tenant_id}:leads_deleted")
            redis_client.incr(f"tenant:{tenant_id}:api_calls")
        except Exception as redis_error:
            logger.warning(f"Failed to increment Redis counters: {redis_error}")
        
        logger.info(f"Lead {lead_id} deleted successfully", 
                   extra={"tenant_id": str(tenant_id), "lead_id": str(lead_id)})
        
        return None
        
    except Exception as e:
        logger.error(f"Error deleting lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete lead"
        )


@router.get("/{lead_id}/timeline", response_model=LeadTimeline)
async def get_lead_timeline(
    lead_id: UUID,
    db: Session = Depends(get_db_session),
    redis_client = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> LeadTimeline:
    """
    Get comprehensive timeline of all lead activities.
    
    Includes chatbot sessions, calls, demos, status changes, enrollments
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Retrieving timeline for lead {lead_id}, tenant {tenant_id}", 
                   extra={"tenant_id": str(tenant_id), "lead_id": str(lead_id)})
        
        # Initialize lead service
        lead_service = LeadService(db=db, redis_client=redis_client, current_user=current_user)
        
        # Get timeline
        timeline = lead_service.get_lead_timeline(lead_id=lead_id)
        
        # Increment usage counter
        try:
            redis_client.incr(f"tenant:{tenant_id}:api_calls")
        except Exception as redis_error:
            logger.warning(f"Failed to increment Redis counters: {redis_error}")
        
        logger.info(f"Timeline for lead {lead_id} retrieved with {len(timeline.events)} events", 
                   extra={"tenant_id": str(tenant_id), "lead_id": str(lead_id)})
        
        return timeline
        
    except Exception as e:
        logger.error(f"Error retrieving timeline for lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve lead timeline"
        )


@router.post("/{lead_id}/assign", response_model=LeadResponse)
async def assign_lead(
    lead_id: UUID,
    mentor_id: UUID,
    db: Session = Depends(get_db_session),
    redis_client = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> LeadResponse:
    """
    Assign lead to a specific mentor.
    
    Validates mentor exists and belongs to same tenant
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Assigning lead {lead_id} to mentor {mentor_id}", 
                   extra={"tenant_id": str(tenant_id), "lead_id": str(lead_id), "mentor_id": str(mentor_id)})
        
        # Initialize lead service
        lead_service = LeadService(db=db, redis_client=redis_client, current_user=current_user)
        
        # Assign lead
        lead = lead_service.assign_lead(
            lead_id=lead_id,
            mentor_id=mentor_id
        )
        
        # Increment usage counter
        try:
            redis_client.incr(f"tenant:{tenant_id}:leads_assigned")
            redis_client.incr(f"tenant:{tenant_id}:api_calls")
        except Exception as redis_error:
            logger.warning(f"Failed to increment Redis counters: {redis_error}")
        
        logger.info(f"Lead {lead_id} assigned successfully to {mentor_id}", 
                   extra={"tenant_id": str(tenant_id), "lead_id": str(lead_id)})
        
        return lead
        
    except ValueError as e:
        logger.error(f"Validation error assigning lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error assigning lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign lead"
        )


@router.post("/{lead_id}/convert", response_model=Dict[str, Any])
async def convert_lead(
    lead_id: UUID,
    enrollment_data: Dict[str, Any],
    db: Session = Depends(get_db_session),
    redis_client = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Convert lead to enrollment.
    
    Creates enrollment record and updates lead status
    """
    try:
        from app.schemas.enrollment import EnrollmentCreate
        
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Converting lead {lead_id} to enrollment", 
                   extra={"tenant_id": str(tenant_id), "lead_id": str(lead_id)})
        
        # Initialize lead service
        lead_service = LeadService(db=db, redis_client=redis_client, current_user=current_user)
        
        # Convert enrollment_data dict to schema
        enrollment_schema = EnrollmentCreate(**enrollment_data)
        
        # Convert lead
        lead, enrollment = lead_service.convert_lead_to_enrollment(
            lead_id=lead_id,
            enrollment_data=enrollment_schema
        )
        
        # Increment usage counters
        try:
            redis_client.incr(f"tenant:{tenant_id}:leads_converted")
            redis_client.incr(f"tenant:{tenant_id}:enrollments_created")
            redis_client.incr(f"tenant:{tenant_id}:api_calls")
        except Exception as redis_error:
            logger.warning(f"Failed to increment Redis counters: {redis_error}")
        
        logger.info(f"Lead {lead_id} converted successfully", 
                   extra={"tenant_id": str(tenant_id), "lead_id": str(lead_id)})
        
        return {
            "lead": lead,
            "enrollment": enrollment,
            "message": "Lead converted successfully"
        }
        
    except ValueError as e:
        logger.error(f"Validation error converting lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error converting lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert lead"
        )
