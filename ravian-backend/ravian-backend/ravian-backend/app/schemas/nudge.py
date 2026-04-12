from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class VoiceNudgeSettings(BaseModel):
    """Settings for voice nudges"""
    voice_id: str = Field(default="nova", description="TTS voice ID")
    send_audio: bool = Field(default=True)
    speed: float = Field(default=1.0, ge=0.25, le=4.0)

class SendNudgeRequest(BaseModel):
    """Request to send a nudge"""
    student_id: UUID
    nudge_type: str = Field(..., description="inactivity_reminder, confusion_help, risk_alert, encouragement")
    message: str = Field(..., min_length=10, max_length=500)
    channel: str = Field(default="in_app", description="in_app, email, sms, voice")
    voice_settings: Optional[VoiceNudgeSettings] = None
    priority: str = Field(default="normal", description="low, normal, high")

class SendNudgeResponse(BaseModel):
    """Response after sending nudge"""
    nudge_id: UUID
    student_id: UUID
    nudge_type: str
    channel: str
    audio_url: Optional[str] = None
    status: str
    sent_at: datetime
    message: str

class NudgeHistoryItem(BaseModel):
    """Single nudge in history"""
    nudge_id: UUID
    nudge_type: str
    message: str
    channel: str
    audio_url: Optional[str] = None
    status: str
    sent_at: datetime
    read_at: Optional[datetime] = None

class NudgeHistoryResponse(BaseModel):
    """Nudge history for a student"""
    student_id: UUID
    nudges: List[NudgeHistoryItem]
    total_nudges: int
    voice_nudges: int
    text_nudges: int
    read_count: int
