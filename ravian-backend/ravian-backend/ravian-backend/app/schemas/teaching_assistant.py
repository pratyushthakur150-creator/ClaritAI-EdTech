"""Pydantic schemas for Teaching Assistant API"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class TAQueryRequest(BaseModel):
    student_id: UUID
    course_id: UUID
    question: str = Field(..., min_length=1, max_length=2000)
    module_id: Optional[UUID] = None
    use_voice: bool = False
    voice_id: str = Field(default="nova", description="alloy, echo, fable, onyx, nova, shimmer")


class TASource(BaseModel):
    document_title: str
    document_type: str
    source_file: str = ""
    page_number: str = ""
    timestamp_label: str = ""
    relevance_score: Optional[float] = None


class TAQueryResponse(BaseModel):
    interaction_id: str
    question: str
    answer: str
    sources: List[TASource] = []
    confidence: float
    rag_used: bool
    audio_url: Optional[str] = None
    transcribed_question: Optional[str] = None


class TAFeedbackRequest(BaseModel):
    interaction_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    helpful: Optional[bool] = None


class TASessionStartRequest(BaseModel):
    student_id: UUID
    course_id: UUID
    voice_settings: Optional[Dict[str, Any]] = {}


class TASessionResponse(BaseModel):
    session_id: str
    status: str
    started_at: datetime
