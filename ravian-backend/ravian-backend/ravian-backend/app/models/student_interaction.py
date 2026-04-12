"""
StudentInteraction Model

Critical SQLAlchemy model for the Teaching Assistant module that tracks all student
interactions with the AI assistant including voice support, RAG context, quality
metrics, and escalation tracking. This model is imported by all major services:
- ConfusionTrackingService
- RiskScoringService  
- HeatmapService
- VoiceConversationService

Author: Teaching Assistant Module
"""

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, 
    ForeignKey, Index, CheckConstraint, func, Enum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any, List
import enum

from .base import Base


class InteractionMode(enum.Enum):
    """Enumeration for student interaction modes"""
    TEXT = "text"
    VOICE = "voice"
    MIXED = "mixed"


class FeedbackRating(enum.Enum):
    """Enumeration for feedback rating values"""
    VERY_POOR = 1
    POOR = 2
    AVERAGE = 3
    GOOD = 4
    EXCELLENT = 5


class StudentInteraction(Base):
    """
    StudentInteraction Model
    
    Stores all student interaction data with the Teaching Assistant including:
    - Query and answer content
    - Voice support with audio URLs and duration
    - RAG (Retrieval-Augmented Generation) context and sources
    - Quality metrics including confidence scores and feedback
    - Escalation tracking to mentors
    - Comprehensive indexing for performance optimization
    
    This model is central to the Teaching Assistant functionality and is used by:
    - Confusion tracking and risk assessment
    - Heatmap generation for learning analytics
    - Voice conversation management
    - Quality assurance and feedback collection
    """
    
    __tablename__ = 'student_interactions'
    __table_args__ = (
        # Composite indexes for performance optimization
        Index('idx_student_interactions_tenant_student', 'tenant_id', 'student_id'),
        Index('idx_student_interactions_student_course', 'student_id', 'course_id'),
        Index('idx_student_interactions_course_module', 'course_id', 'module_id'),
        Index('idx_student_interactions_tenant_course', 'tenant_id', 'course_id'),
        Index('idx_student_interactions_module_topic', 'module_id', 'topic'),
        Index('idx_student_interactions_confidence_created', 'confidence', 'created_at'),
        Index('idx_student_interactions_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_student_interactions_student_created', 'student_id', 'created_at'),
        Index('idx_student_interactions_mode_audio', 'mode', 'audio_url'),
        Index('idx_student_interactions_escalated_created', 'escalated_to_mentor', 'created_at'),
        
        # Check constraints for data validation
        CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', name='chk_confidence_range'),
        CheckConstraint('feedback >= 1 AND feedback <= 5', name='chk_feedback_range'),
        CheckConstraint('audio_duration_seconds >= 0', name='chk_audio_duration_positive'),
        
        # Allow extending existing table structure
        {'extend_existing': True}
    )
    
    # =====================================================================
    # PRIMARY IDENTIFIERS (UUID fields)
    # =====================================================================
    
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        server_default=func.gen_random_uuid(),
        comment="Primary key identifier for the student interaction"
    )
    
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('tenants.id', ondelete='CASCADE'), 
        nullable=False,
        comment="Foreign key reference to tenants table for multi-tenancy support"
    )
    
    student_id = Column(
        UUID(as_uuid=True), 
        nullable=False,
        comment="UUID identifier of the student who initiated the interaction"
    )
    
    course_id = Column(
        UUID(as_uuid=True), 
        nullable=False,
        comment="UUID identifier of the course context for this interaction"
    )
    
    module_id = Column(
        UUID(as_uuid=True), 
        nullable=True,
        comment="UUID identifier of the specific module within the course"
    )
    
    # =====================================================================
    # QUERY AND ANSWER DATA FIELDS
    # =====================================================================
    
    query = Column(
        Text, 
        nullable=False,
        comment="The original question or prompt submitted by the student"
    )
    
    answer = Column(
        Text, 
        nullable=False,
        comment="The response provided by the Teaching Assistant AI"
    )
    
    topic = Column(
        String(255), 
        nullable=True,
        comment="The identified topic or subject area for this interaction"
    )
    
    # =====================================================================
    # VOICE SUPPORT FIELDS
    # =====================================================================
    
    mode = Column(
        Enum(InteractionMode, name='interaction_mode_enum'), 
        nullable=False, 
        default=InteractionMode.TEXT,
        comment="Mode of interaction: text, voice, or mixed input/output"
    )
    
    audio_url = Column(
        String(500), 
        nullable=True,
        comment="URL to the audio recording of the student's question (for voice interactions)"
    )
    
    audio_duration_seconds = Column(
        Integer, 
        nullable=True,
        comment="Duration of the audio recording in seconds"
    )
    
    # =====================================================================
    # RAG CONTEXT FIELDS (JSONB for PostgreSQL)
    # =====================================================================
    
    context = Column(
        JSONB, 
        nullable=True, 
        default={},
        comment="RAG context data including retrieved documents and metadata stored as JSONB"
    )
    
    sources = Column(
        JSONB, 
        nullable=True, 
        default=[],
        comment="Array of source documents and references used for generating the answer"
    )
    
    # =====================================================================
    # QUALITY METRICS
    # =====================================================================
    
    confidence = Column(
        Float, 
        nullable=True,
        comment="AI confidence score for the generated answer (0.0 to 1.0)"
    )
    
    feedback = Column(
        Integer, 
        nullable=True,
        comment="Student feedback rating for the answer quality (1 to 5 stars)"
    )
    
    feedback_comment = Column(
        Text, 
        nullable=True,
        comment="Optional written feedback comment from the student"
    )
    
    # =====================================================================
    # ESCALATION TRACKING
    # =====================================================================
    
    escalated_to_mentor = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="Flag indicating if this interaction was escalated to a human mentor"
    )
    
    # =====================================================================
    # TIMESTAMPS (timezone-aware)
    # =====================================================================
    
    created_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp(),
        comment="Timestamp when the interaction was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True), 
        nullable=True, 
        onupdate=func.current_timestamp(),
        comment="Timestamp when the interaction was last updated"
    )
    
    # =====================================================================
    # HELPER METHODS
    # =====================================================================
    
    def is_confused(self, threshold: float = 0.7) -> bool:
        """
        Determine if the student appears confused based on confidence score.
        
        Args:
            threshold (float): Confidence threshold below which student is considered confused
            
        Returns:
            bool: True if confidence is below threshold, False otherwise
        """
        if self.confidence is None:
            return False
        return self.confidence < threshold
    
    def is_voice_mode(self) -> bool:
        """
        Check if this interaction involved voice input or output.
        
        Returns:
            bool: True if mode is VOICE or MIXED, False for TEXT only
        """
        return self.mode in [InteractionMode.VOICE, InteractionMode.MIXED]
    
    def has_audio(self) -> bool:
        """
        Check if this interaction has associated audio content.
        
        Returns:
            bool: True if audio_url is present, False otherwise
        """
        return self.audio_url is not None and len(self.audio_url.strip()) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the interaction to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary containing all interaction data
        """
        return {
            'id': str(self.id) if self.id else None,
            'tenant_id': str(self.tenant_id) if self.tenant_id else None,
            'student_id': str(self.student_id) if self.student_id else None,
            'course_id': str(self.course_id) if self.course_id else None,
            'module_id': str(self.module_id) if self.module_id else None,
            'query': self.query,
            'answer': self.answer,
            'topic': self.topic,
            'mode': self.mode.value if self.mode else None,
            'audio_url': self.audio_url,
            'audio_duration_seconds': self.audio_duration_seconds,
            'context': self.context,
            'sources': self.sources,
            'confidence': self.confidence,
            'feedback': self.feedback,
            'feedback_comment': self.feedback_comment,
            'escalated_to_mentor': self.escalated_to_mentor,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_confused': self.is_confused(),
            'is_voice_mode': self.is_voice_mode(),
            'has_audio': self.has_audio()
        }
    
    @classmethod
    def create_interaction(
        cls, 
        tenant_id: str,
        student_id: str,
        course_id: str,
        query: str,
        answer: str,
        module_id: Optional[str] = None,
        topic: Optional[str] = None,
        mode: InteractionMode = InteractionMode.TEXT,
        audio_url: Optional[str] = None,
        audio_duration_seconds: Optional[int] = None,
        context: Optional[Dict] = None,
        sources: Optional[List] = None,
        confidence: Optional[float] = None
    ) -> 'StudentInteraction':
        """
        Factory method to create a new StudentInteraction instance.
        
        Args:
            tenant_id: UUID of the tenant
            student_id: UUID of the student
            course_id: UUID of the course
            query: Student's question
            answer: AI's response
            module_id: Optional UUID of the module
            topic: Optional topic classification
            mode: Interaction mode (text/voice/mixed)
            audio_url: Optional URL to audio recording
            audio_duration_seconds: Optional audio duration
            context: Optional RAG context data
            sources: Optional source documents
            confidence: Optional confidence score
            
        Returns:
            StudentInteraction: New interaction instance
        """
        return cls(
            tenant_id=tenant_id,
            student_id=student_id,
            course_id=course_id,
            module_id=module_id,
            query=query,
            answer=answer,
            topic=topic,
            mode=mode,
            audio_url=audio_url,
            audio_duration_seconds=audio_duration_seconds,
            context=context or {},
            sources=sources or [],
            confidence=confidence
        )
    
    def update_feedback(self, rating: int, comment: Optional[str] = None) -> None:
        """
        Update the feedback rating and comment for this interaction.
        
        Args:
            rating: Feedback rating (1-5)
            comment: Optional feedback comment
            
        Raises:
            ValueError: If rating is not between 1 and 5
        """
        if not (1 <= rating <= 5):
            raise ValueError("Feedback rating must be between 1 and 5")
        
        self.feedback = rating
        self.feedback_comment = comment
        self.updated_at = datetime.utcnow()
    
    def escalate_to_mentor(self) -> None:
        """Mark this interaction as escalated to a human mentor."""
        self.escalated_to_mentor = True
        self.updated_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        """String representation of the StudentInteraction."""
        return (
            f"<StudentInteraction(id={self.id}, student_id={self.student_id}, "
            f"course_id={self.course_id}, topic='{self.topic}', "
            f"mode={self.mode.value if self.mode else None}, "
            f"confidence={self.confidence}, created_at={self.created_at})>"
        )


# Additional indexes for frequently queried combinations
# These will be created automatically when the table is created

__all__ = ['StudentInteraction', 'InteractionMode', 'FeedbackRating', 'Base']