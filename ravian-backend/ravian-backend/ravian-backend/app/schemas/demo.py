"""
Demo Schemas - Pydantic models for demo management
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class DemoBase(BaseModel):
    """Base demo schema"""
    lead_id: UUID
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=15, le=240)
    timezone: Optional[str] = None
    platform: Optional[str] = None  # Zoom, Teams, Meet, etc.
    meeting_link: Optional[str] = None
    notes: Optional[str] = None


class DemoCreate(DemoBase):
    """Schema for creating a demo"""
    course_id: Optional[UUID] = None
    mentor_id: Optional[UUID] = None



class DemoUpdate(BaseModel):
    """Schema for updating a demo"""
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=240)
    timezone: Optional[str] = None
    completed: Optional[bool] = None
    attended: Optional[bool] = None
    outcome: Optional[str] = None  # enrolled, interested, not_interested, reschedule, no_show
    interest_level: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None
    courses_demonstrated: Optional[Dict[str, Any]] = None
    questions_asked: Optional[Dict[str, Any]] = None
    objections: Optional[Dict[str, Any]] = None
    follow_up_scheduled: Optional[datetime] = None
    next_steps: Optional[str] = None
    platform: Optional[str] = None
    meeting_link: Optional[str] = None
    recording_url: Optional[str] = None


def _enum_to_str(v: Any) -> Any:
    """Convert SQLAlchemy/Python enum to string for JSON serialization."""
    if v is None:
        return v
    if hasattr(v, "value"):
        return v.value
    return v


class DemoResponse(DemoBase):
    """Schema for demo responses"""
    id: UUID
    completed: bool = False
    attended: Optional[bool] = None
    attendee_count: int = 1
    outcome: Optional[str] = None
    interest_level: Optional[int] = None
    courses_demonstrated: Optional[Dict[str, Any]] = None
    questions_asked: Optional[Dict[str, Any]] = None
    objections: Optional[Dict[str, Any]] = None
    follow_up_scheduled: Optional[datetime] = None
    next_steps: Optional[str] = None
    recording_url: Optional[str] = None
    google_event_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("outcome", mode="before")
    @classmethod
    def convert_enum_to_str(cls, v: Any) -> Any:
        return _enum_to_str(v)

    class Config:
        from_attributes = True


class DemoListResponse(BaseModel):
    """Schema for paginated demo list"""
    data: List[DemoResponse]
    pagination: Dict[str, Any]

    class Config:
        from_attributes = True


class DemoOutcomeRequest(BaseModel):
    """Schema for recording demo outcome"""
    attended: bool
    outcome: str  # enrolled, interested, not_interested, reschedule, no_show
    interest_level: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None
    follow_up_scheduled: Optional[datetime] = None
    next_steps: Optional[str] = None