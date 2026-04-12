from pydantic import BaseModel, Field
from typing import List
from uuid import UUID

class ModuleConfusionData(BaseModel):
    """Confusion data for a single module"""
    module_id: UUID
    module_name: str
    confusion_score: float = Field(..., description="0-100, higher = more confusion")
    question_count: int
    student_count: int
    avg_confidence: float
    top_confused_topics: List[str]

class HeatmapResponse(BaseModel):
    """Heatmap data for course visualization"""
    course_id: UUID
    modules: List[ModuleConfusionData]
    overall_confusion_score: float
    most_confused_module: str
    least_confused_module: str
