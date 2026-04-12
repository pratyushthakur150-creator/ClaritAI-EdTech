"""
Enrollment API router for AI EdTech CRM platform.
Handles enrollment creation, updates, listing, and teaching assistant activation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
import redis
import logging

# CORRECTED IMPORTS for your backend structure
from app.core.database import get_db_session
from app.core.redis_client import get_redis_client
from app.core.utils import get_tenant_id, get_user_id
from app.dependencies.auth import get_current_user

# Import schemas
from app.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse

# Import service
from app.services.enrollment_service import EnrollmentService

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post("/", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def create_enrollment(
    enrollment_data: EnrollmentCreate,
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create new enrollment by converting a lead to student.
    
    This endpoint:
    1. Creates enrollment record
    2. Updates lead status to 'enrolled' 
    3. Creates student record for LMS access
    4. Logs analytics events
    5. Sends LMS credentials email
    
    Returns the created enrollment with nested lead and course data.
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Creating enrollment for lead {enrollment_data.lead_id}")
        
        # Initialize enrollment service
        enrollment_service = EnrollmentService(
            db=db,
            redis_client=redis_client,
            tenant_id=tenant_id
        )
        
        enrollment = enrollment_service.create_enrollment(enrollment_data=enrollment_data)
        
        logger.info(f"Enrollment created successfully: {enrollment.id}")
        return enrollment
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating enrollment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create enrollment"
        )


@router.get("/", response_model=Dict[str, Any])
async def list_enrollments(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status (pending/partial/completed)"),
    course_id: Optional[str] = Query(None, description="Filter by course ID"),
    enrolled_after: Optional[datetime] = Query(None, description="Filter enrollments after this date"),
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List enrollments with pagination and filtering.
    
    Supports filtering by:
    - payment_status: pending, partial, completed
    - course_id: UUID of the course
    - enrolled_after: datetime filter for enrollment date
    
    Returns paginated list with metadata.
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Listing enrollments for tenant {tenant_id}, page {page}")
        
        # Parse course_id if provided
        parsed_course_id = None
        if course_id:
            try:
                parsed_course_id = UUID(course_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Course ID must be a valid UUID"
                )
        
        # Validate payment_status if provided
        # Validate payment_status if provided
        if payment_status:
            payment_status = payment_status.upper()
            if payment_status not in {"PENDING", "PARTIAL", "PAID", "FAILED", "REFUNDED", "CANCELLED"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment status must be one of: pending, partial, paid, failed, refunded, cancelled"
                )
        
        # Initialize enrollment service
        enrollment_service = EnrollmentService(
            db=db,
            redis_client=redis_client,
            tenant_id=tenant_id
        )
        
        enrollments, total = enrollment_service.get_enrollments(
            page=page,
            per_page=per_page,
            payment_status=payment_status,
            course_id=parsed_course_id,
            enrolled_after=enrolled_after
        )
        
        total_pages = (total + per_page - 1) // per_page
        
        # Build filters applied object
        filters_applied = {}
        if payment_status:
            filters_applied["payment_status"] = payment_status
        if course_id:
            filters_applied["course_id"] = course_id
        if enrolled_after:
            filters_applied["enrolled_after"] = enrolled_after.isoformat()
        
        response = {
            "enrollments": enrollments,
            "total": total,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "filters_applied": filters_applied
        }
        
        logger.info(f"Retrieved {len(enrollments)} enrollments for tenant {tenant_id}")
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error listing enrollments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve enrollments"
        )


@router.get("/{enrollment_id}", response_model=EnrollmentResponse)
async def get_enrollment(
    enrollment_id: UUID,
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get single enrollment by ID with nested lead, course, and student data.
    
    Returns complete enrollment details including:
    - Lead information (id, name, phone)
    - Course information (id, name)
    - Payment details and status
    - Student ID if created
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Retrieving enrollment {enrollment_id} for tenant {tenant_id}")
        
        # Initialize enrollment service
        enrollment_service = EnrollmentService(
            db=db,
            redis_client=redis_client,
            tenant_id=tenant_id
        )
        
        enrollment = enrollment_service.get_enrollment_by_id(enrollment_id=enrollment_id)
        
        logger.info(f"Enrollment {enrollment_id} retrieved successfully")
        return enrollment
        
    except ValueError as e:
        logger.error(f"Enrollment not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving enrollment {enrollment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve enrollment"
        )


@router.patch("/{enrollment_id}", response_model=EnrollmentResponse)
async def update_enrollment(
    enrollment_id: UUID,
    update_data: EnrollmentUpdate,
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update enrollment payment status, amount paid, or notes.
    
    Automatically updates payment_status based on amount_paid if not explicitly provided:
    - amount_paid = 0: status = pending
    - amount_paid >= total_amount: status = completed  
    - 0 < amount_paid < total_amount: status = partial
    
    Logs analytics events for payment updates.
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Updating enrollment {enrollment_id} for tenant {tenant_id}")
        
        # Initialize enrollment service
        enrollment_service = EnrollmentService(
            db=db,
            redis_client=redis_client,
            tenant_id=tenant_id
        )
        
        enrollment = enrollment_service.update_enrollment(
            enrollment_id=enrollment_id,
            update_data=update_data
        )
        
        logger.info(f"Enrollment {enrollment_id} updated successfully")
        return enrollment
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating enrollment {enrollment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update enrollment"
        )


@router.post("/{enrollment_id}/activate-assistant", response_model=Dict[str, Any])
async def activate_teaching_assistant(
    enrollment_id: UUID,
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Activate teaching assistant for the enrolled student.
    
    This endpoint:
    1. Creates student record if not exists
    2. Enables assistant_enabled flag
    3. Generates access token for assistant interface
    4. Returns student ID, LMS credentials, and access token
    
    Required for students to access AI teaching assistant features.
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Activating teaching assistant for enrollment {enrollment_id}")
        
        # Initialize enrollment service
        enrollment_service = EnrollmentService(
            db=db,
            redis_client=redis_client,
            tenant_id=tenant_id
        )
        
        result = enrollment_service.activate_teaching_assistant(enrollment_id=enrollment_id)
        
        logger.info(f"Teaching assistant activated for enrollment {enrollment_id}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error activating teaching assistant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate teaching assistant"
        )


@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_enrollment_statistics(
    db: Session = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get enrollment statistics for tenant dashboard.
    
    Returns:
    - Total enrollments
    - Payment status breakdown (pending/partial/completed counts)
    - Revenue statistics (total, collected, outstanding)
    """
    try:
        tenant_id = get_tenant_id(current_user)
        
        logger.info(f"Fetching enrollment statistics for tenant {tenant_id}")
        
        # Initialize enrollment service
        enrollment_service = EnrollmentService(
            db=db,
            redis_client=redis_client,
            tenant_id=tenant_id
        )
        
        stats = enrollment_service.get_enrollment_statistics()
        
        logger.info(f"Enrollment statistics retrieved for tenant {tenant_id}")
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching enrollment statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch enrollment statistics"
        )