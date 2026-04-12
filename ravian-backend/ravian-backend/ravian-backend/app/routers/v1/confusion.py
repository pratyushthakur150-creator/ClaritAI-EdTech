from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
from uuid import UUID

from app.core.database import get_db_session
from app.core.utils import get_tenant_id
from app.dependencies.auth import get_current_user
from app.schemas.confusion import (
    TopConfusionTopicsResponse,
    StudentConfusionResponse
)
from app.services.confusion_tracking_service import ConfusionTrackingService

router = APIRouter(prefix="/confusion", tags=["Confusion Tracking"])

@router.get("/top-topics/{course_id}", response_model=TopConfusionTopicsResponse)
async def get_top_confused_topics(
    course_id: UUID,
    limit: int = Query(default=10, ge=1, le=50),
    days_back: int = Query(default=30, ge=1, le=365),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get the most confused topics in a course.
    
    Analyzes student interactions to identify topics with:
    - Low confidence scores
    - Repeated questions
    - Escalations to mentors
    
    Args:
        course_id: UUID of the course to analyze
        limit: Maximum number of topics to return (1-50)
        days_back: Number of days to look back for analysis (1-365)
        current_user: JWT authenticated user data (injected by RequireAuth)
        db: Database session (injected by get_db dependency)
    
    Returns:
        TopConfusionTopicsResponse: List of most confused topics with statistics
    
    Raises:
        HTTPException: If database query fails or authentication issues
    """
    tenant_id = get_tenant_id(current_user)
    
    service = ConfusionTrackingService(db)
    result = service.get_top_confused_topics(
        course_id=course_id,
        tenant_id=tenant_id,
        limit=limit,
        days_back=days_back
    )
    
    return TopConfusionTopicsResponse(**result)

@router.get("/student/{student_id}", response_model=StudentConfusionResponse)
async def get_student_confusion_patterns(
    student_id: UUID,
    course_id: UUID = Query(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get confusion patterns for a specific student.
    
    Shows which topics the student struggles with and risk level.
    Analyzes:
    - Question patterns by topic
    - Average confidence scores
    - Escalation history
    - Risk assessment (low/medium/high)
    
    Args:
        student_id: UUID of the student to analyze
        course_id: UUID of the course context (required query parameter)
        current_user: JWT authenticated user data (injected by RequireAuth)
        db: Database session (injected by get_db dependency)
    
    Returns:
        StudentConfusionResponse: Student's confusion patterns and risk level
    
    Raises:
        HTTPException: If database query fails or authentication issues
    """
    tenant_id = get_tenant_id(current_user)
    
    service = ConfusionTrackingService(db)
    result = service.get_student_confusion(
        student_id=student_id,
        course_id=course_id,
        tenant_id=tenant_id
    )
    
    return StudentConfusionResponse(**result)
