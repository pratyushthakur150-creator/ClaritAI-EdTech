from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from uuid import UUID

from app.core.database import get_db_session
from app.core.utils import get_tenant_id
from app.dependencies.auth import get_current_user
from app.schemas.nudge import (
    SendNudgeRequest,
    SendNudgeResponse,
    NudgeHistoryResponse
)
from app.services.nudge_service import NudgeService

router = APIRouter(prefix="/nudges")

@router.post("/send", response_model=SendNudgeResponse)
async def send_nudge(
    request: SendNudgeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Send a proactive nudge to a student with voice TTS support.
    
    Supports multiple delivery channels:
    - in_app: In-application notification
    - email: Email delivery (requires email service integration)  
    - sms: SMS delivery (requires SMS service integration)
    - voice: Text-to-speech audio nudge with customizable voice settings
    
    Nudge types supported:
    - inactivity_reminder: Remind students who haven't logged in recently
    - confusion_help: Offer help to students struggling with specific topics
    - risk_alert: Alert high-risk students who may need immediate intervention
    - encouragement: Send positive reinforcement and motivation messages
    
    Voice settings (for voice channel):
    - voice_id: TTS voice identifier (default: "nova")
    - send_audio: Whether to generate audio file (default: True)
    - speed: Speech speed from 0.25x to 4.0x (default: 1.0)
    
    Priority levels:
    - low: Non-urgent nudges, delivered during regular hours
    - normal: Standard priority nudges (default)
    - high: Urgent nudges requiring immediate attention
    
    Args:
        request: SendNudgeRequest containing nudge details
        current_user: Authenticated user from JWT token
        db: Database session for data persistence
        
    Returns:
        SendNudgeResponse: Confirmation with nudge ID, delivery status, and audio URL if voice
        
    Raises:
        HTTPException: On authentication failures, invalid requests, or service errors
    """
    tenant_id = get_tenant_id(current_user)
    
    # Initialize voice service only for voice channel requests
    voice_service = None
    if request.channel == "voice":
        try:
            from app.services.voice_service import VoiceService
            voice_service = VoiceService()
        except ImportError:
            # Voice service not available, will fall back to in_app
            voice_service = None
    
    nudge_service = NudgeService(db=db, voice_service=voice_service)
    
    result = await nudge_service.send_nudge(
        student_id=request.student_id,
        nudge_type=request.nudge_type,
        message=request.message,
        channel=request.channel,
        tenant_id=tenant_id,
        voice_settings=request.voice_settings.dict() if request.voice_settings else None,
        priority=request.priority
    )
    
    return SendNudgeResponse(**result)

@router.get("/history/{student_id}", response_model=NudgeHistoryResponse)
async def get_nudge_history(
    student_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Retrieve complete nudge history for a specific student.
    
    Returns comprehensive history including:
    - All nudge types (inactivity, confusion help, risk alerts, encouragement)
    - Multiple delivery channels (in_app, email, sms, voice)
    - Voice nudges with audio URLs for playback
    - Read/unread status and timestamps
    - Delivery status and statistics
    
    The response includes summary statistics:
    - total_nudges: Total number of nudges sent to student
    - voice_nudges: Count of voice/audio nudges
    - text_nudges: Count of text-based nudges (in_app, email, sms)
    - read_count: Number of nudges marked as read by student
    
    Results are ordered by sent_at timestamp (most recent first) and limited
    to the most recent 50 nudges for performance.
    
    Multi-tenant security ensures only nudges for the authenticated tenant
    are returned, protecting student privacy across different organizations.
    
    Args:
        student_id: UUID of the student whose history to retrieve
        current_user: Authenticated user from JWT token
        db: Database session for data access
        
    Returns:
        NudgeHistoryResponse: Complete nudge history with statistics
        
    Raises:
        HTTPException: On authentication failures or database errors
    """
    tenant_id = get_tenant_id(current_user)
    
    nudge_service = NudgeService(db=db)
    result = nudge_service.get_nudge_history(
        student_id=student_id,
        tenant_id=tenant_id
    )
    
    return NudgeHistoryResponse(**result)

@router.post("/send-automated/{course_id}")
async def send_automated_nudges(
    course_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Send automated nudges to at-risk students in a course.
    
    This endpoint triggers the automated nudge system that:
    1. Analyzes students using the RiskScoringService
    2. Identifies high and critical risk students
    3. Sends appropriate nudges based on risk level
    4. Provides summary of actions taken
    
    Typically called by scheduled tasks, cron jobs, or manual triggers
    by instructors/administrators to proactively engage at-risk students.
    
    Risk-based nudge logic:
    - Critical risk students: Urgent intervention messages with high priority
    - High risk students: Supportive messages with normal priority
    - Focuses on students with risk scores >= 60
    
    Args:
        course_id: UUID of the course to analyze for at-risk students
        current_user: Authenticated user from JWT token
        db: Database session for data access
        
    Returns:
        dict: Summary including students analyzed, nudges sent, risk counts
        
    Raises:
        HTTPException: On authentication failures or service errors
    """
    tenant_id = get_tenant_id(current_user)
    
    nudge_service = NudgeService(db=db)
    result = await nudge_service.send_automated_nudges(
        course_id=course_id,
        tenant_id=tenant_id
    )
    
    return result

@router.patch("/mark-read/{nudge_id}")
async def mark_nudge_as_read(
    nudge_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Mark a specific nudge as read by the student.
    
    Updates the nudge record with a read timestamp, allowing the system
    to track student engagement with nudges and calculate read rates.
    
    This endpoint is typically called when:
    - Student opens/views an in-app nudge
    - Student clicks on email nudge links
    - Student interacts with voice nudge playback
    - Frontend applications track nudge visibility
    
    Multi-tenant security ensures only nudges belonging to the
    authenticated tenant can be marked as read.
    
    Args:
        nudge_id: UUID of the nudge to mark as read
        current_user: Authenticated user from JWT token
        db: Database session for data updates
        
    Returns:
        dict: Success confirmation with read status
        
    Raises:
        HTTPException: On nudge not found, authentication failures, or database errors
    """
    tenant_id = get_tenant_id(current_user)
    
    nudge_service = NudgeService(db=db)
    success = nudge_service.mark_nudge_as_read(
        nudge_id=nudge_id,
        tenant_id=tenant_id
    )
    
    return {
        "nudge_id": nudge_id,
        "marked_as_read": success,
        "timestamp": "2024-01-15T10:30:00Z"  # This would be actual timestamp in production
    }
