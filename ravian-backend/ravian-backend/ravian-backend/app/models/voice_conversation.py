from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from .base import Base

class VoiceConversation(Base):
    """
    SQLAlchemy model for voice conversations in the Teaching Assistant module.
    Tracks voice-based learning sessions between students and the AI assistant.
    """
    __tablename__ = 'voice_conversations'
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    student_id = Column(UUID(as_uuid=True), nullable=False)
    course_id = Column(UUID(as_uuid=True), nullable=False)
    session_id = Column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4)
    
    # Session tracking fields
    status = Column(String(20), nullable=False, default='active')  # active, completed, interrupted
    voice_settings = Column(JSONB)  # Voice configuration, language preferences, etc.
    turn_count = Column(Integer, default=0, nullable=False)  # Number of conversation turns
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    ended_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    __table_args__ = (
        # Composite indexes for efficient querying
        Index('idx_voice_conv_tenant_student', 'tenant_id', 'student_id'),
        Index('idx_voice_conv_course_status', 'course_id', 'status'),
        Index('idx_voice_conv_tenant_course', 'tenant_id', 'course_id'),
        Index('idx_voice_conv_student_started', 'student_id', 'started_at'),
        
        # Single column indexes
        Index('idx_voice_conv_tenant_id', 'tenant_id'),
        Index('idx_voice_conv_status', 'status'),
        Index('idx_voice_conv_started_at', 'started_at'),
        Index('idx_voice_conv_session_id', 'session_id'),  # Unique constraint will create index
        
        # Unique constraint for session_id
        UniqueConstraint('session_id', name='uq_voice_conv_session_id'),
        
        {'extend_existing': True}
    )
    
    def to_dict(self):
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'student_id': str(self.student_id),
            'course_id': str(self.course_id),
            'session_id': str(self.session_id),
            'status': self.status,
            'voice_settings': self.voice_settings,
            'turn_count': self.turn_count,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_conversation(cls, tenant_id, student_id, course_id, voice_settings=None):
        """Factory method to create a new voice conversation"""
        return cls(
            tenant_id=tenant_id,
            student_id=student_id,
            course_id=course_id,
            voice_settings=voice_settings or {},
            status='active'
        )
    
    def end_conversation(self):
        """Mark conversation as completed"""
        self.status = 'completed'
        self.ended_at = func.now()
    
    def increment_turn_count(self):
        """Increment the conversation turn counter"""
        self.turn_count += 1
    
    def __repr__(self):
        return f"<VoiceConversation(id={self.id}, session_id={self.session_id}, status='{self.status}', turns={self.turn_count})>"