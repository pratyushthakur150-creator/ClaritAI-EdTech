"""
Call Schemas - Pydantic models for call management
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class CallLogBase(BaseModel):
    """Base call log schema"""
    lead_id: UUID
    call_direction: str  # inbound, outbound
    duration: Optional[int] = None  # seconds
    phone_number: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None  # positive, neutral, negative
    outcome: str  # connected, no_answer, voicemail, etc.
    recording_url: Optional[str] = None
    cost: Optional[float] = None
    notes: Optional[str] = None
    follow_up_required: bool = False
    next_action: Optional[str] = None
    key_topics: Optional[Dict[str, Any]] = None
    questions_asked: Optional[Dict[str, Any]] = None
    objections: Optional[Dict[str, Any]] = None


class CallLogCreate(CallLogBase):
    """Schema for creating a call log"""
    pass


class CallLogUpdate(BaseModel):
    """Schema for updating a call log"""
    duration: Optional[int] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    outcome: Optional[str] = None
    recording_url: Optional[str] = None
    notes: Optional[str] = None
    follow_up_required: Optional[bool] = None
    next_action: Optional[str] = None


def _enum_to_str(v: Any) -> Any:
    """Convert SQLAlchemy/Python enum to string for JSON serialization."""
    if v is None:
        return v
    if hasattr(v, "value"):
        return v.value
    return v


class CallLogResponse(CallLogBase):
    """Schema for call log responses"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    @field_validator("call_direction", "sentiment", "outcome", mode="before")
    @classmethod
    def convert_enum_to_str(cls, v: Any) -> Any:
        return _enum_to_str(v)

    class Config:
        from_attributes = True


class CallLogListResponse(BaseModel):
    """Schema for paginated call log list"""
    data: List[CallLogResponse]
    pagination: Dict[str, Any]

    class Config:
        from_attributes = True


class TriggerCallRequest(BaseModel):
    """Schema for triggering an AI call"""
    lead_id: UUID
    priority: str = Field(default="medium", description="Call priority: low, medium, high, urgent")
    scheduled_at: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = None


class TriggerCallResponse(BaseModel):
    """Schema for call trigger response"""
    call_id: UUID
    status: str
    message: str
    scheduled_at: Optional[datetime] = None