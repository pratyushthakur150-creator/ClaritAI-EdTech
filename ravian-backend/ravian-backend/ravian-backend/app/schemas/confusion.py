from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class ConfusionTopic(BaseModel):
    """A topic that students are confused about"""
    topic: str
    confusion_count: int = Field(..., description="Number of confused interactions")
    student_count: int = Field(..., description="Number of students confused")
    avg_confidence: float = Field(..., description="Average confidence score")
    recent_questions: List[str] = Field(default_factory=list)
    module_id: Optional[UUID] = None
    module_name: Optional[str] = None

class TopConfusionTopicsResponse(BaseModel):
    """Top confused topics for a course"""
    course_id: UUID
    topics: List[ConfusionTopic]
    total_confusion_signals: int
    date_range: str

class StudentConfusionPattern(BaseModel):
    """Confusion pattern for a single student"""
    topic: str
    question_count: int
    avg_confidence: float
    last_asked: datetime
    escalated: bool

class StudentConfusionResponse(BaseModel):
    """Student's confusion patterns"""
    student_id: UUID
    course_id: UUID
    confusion_patterns: List[StudentConfusionPattern]
    total_confused_topics: int
    risk_level: str  # 'low', 'medium', 'high'
