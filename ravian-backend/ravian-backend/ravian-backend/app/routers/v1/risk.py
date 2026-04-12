from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
from uuid import UUID

from app.core.database import get_db_session
from app.core.utils import get_tenant_id
from app.dependencies.auth import get_current_user
from app.schemas.risk import (
    AtRiskStudentsResponse,
    RiskNotifyRequest,
    RiskNotifyResponse
)
from app.services.risk_scoring_service import RiskScoringService

router = APIRouter(prefix="/risk", tags=["Risk Scoring"])

@router.get("/students/{course_id}", response_model=AtRiskStudentsResponse)
async def get_at_risk_students(
    course_id: UUID,
    min_risk_score: float = Query(default=40, ge=0, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get list of at-risk students in a course.
    
    Risk factors include:
    - Inactivity (days since last login)
    - Low confidence scores
    - Multiple confused topics
    - Escalations to mentors
    - Low engagement
    
    Args:
        course_id: UUID of the course to analyze
        min_risk_score: Minimum risk score threshold (0-100)
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        AtRiskStudentsResponse: List of at-risk students with risk factors
        
    Raises:
        HTTPException: On service errors or authentication issues
    """
    tenant_id = get_tenant_id(current_user)
    
    service = RiskScoringService(db)
    result = service.get_at_risk_students(
        course_id=course_id,
        tenant_id=tenant_id,
        min_risk_score=min_risk_score
    )
    
    return AtRiskStudentsResponse(**result)

@router.post("/notify", response_model=RiskNotifyResponse)
async def notify_mentor_about_student(
    request: RiskNotifyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Send notification to mentor about an at-risk student.
    
    Creates a notification record for mentors about students who need
    immediate attention based on their risk factors and scores.
    
    Risk notification includes:
    - Student identification and current risk score
    - Specific risk factors (inactivity, low confidence, confusion patterns)
    - Recommended actions for mentor intervention
    - Timestamp of notification
    
    Args:
        request: RiskNotifyRequest with student_id, course_id, and optional message
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        RiskNotifyResponse: Confirmation of notification with details
        
    Raises:
        HTTPException: On service errors, invalid student/course, or auth issues
    """
    tenant_id = get_tenant_id(current_user)
    
    service = RiskScoringService(db)
    result = service.notify_mentor(
        student_id=request.student_id,
        course_id=request.course_id,
        tenant_id=tenant_id,
        custom_message=request.message
    )
    
    return RiskNotifyResponse(**result)
