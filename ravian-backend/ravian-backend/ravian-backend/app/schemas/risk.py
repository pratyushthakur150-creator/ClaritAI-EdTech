from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class RiskFactor(BaseModel):
    """Individual risk factor"""
    factor: str
    score: float = Field(..., ge=0, le=100)
    description: str

class AtRiskStudent(BaseModel):
    """Student identified as at-risk"""
    student_id: UUID
    student_name: str
    email: str
    risk_score: float = Field(..., description="0-100, higher = more risk")
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    risk_factors: List[RiskFactor]
    days_inactive: int
    confusion_topics: int
    avg_confidence: float
    last_active: Optional[datetime]
    mentor_notified: bool

class AtRiskStudentsResponse(BaseModel):
    """List of at-risk students"""
    course_id: UUID
    students: List[AtRiskStudent]
    total_at_risk: int
    critical_count: int
    high_count: int
    medium_count: int

class RiskNotifyRequest(BaseModel):
    """Request to notify mentor about at-risk student"""
    student_id: UUID
    course_id: UUID
    message: Optional[str] = Field(None, description="Custom message to mentor")

class RiskNotifyResponse(BaseModel):
    """Response after notifying mentor"""
    student_id: UUID
    mentor_notified: bool
    notification_sent_at: datetime
    message: str
