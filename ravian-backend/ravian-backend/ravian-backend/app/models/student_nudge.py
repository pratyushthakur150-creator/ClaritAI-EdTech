from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Float, ForeignKey, Index, UniqueConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import enum
import uuid
from datetime import datetime

from .base import Base

# Enum definitions for StudentNudge
class NudgeType(enum.Enum):
    INACTIVITY_REMINDER = 'inactivity_reminder'
    CONFUSION_HELP = 'confusion_help'
    RISK_ALERT = 'risk_alert'
    ENCOURAGEMENT = 'encouragement'

class Channel(enum.Enum):
    IN_APP = 'in_app'
    EMAIL = 'email'
    SMS = 'sms'
    VOICE = 'voice'

class Priority(enum.Enum):
    LOW = 'low'
    NORMAL = 'normal'
    HIGH = 'high'

class NudgeStatus(enum.Enum):
    SENT = 'sent'
    DELIVERED = 'delivered'
    READ = 'read'
    FAILED = 'failed'

class StudentNudge(Base):
    """
    SQLAlchemy model for tracking student nudges in the Teaching Assistant system.
    
    This table stores nudging interactions sent to students including reminders,
    help suggestions, risk alerts, and encouragement messages across various channels.
    """
    __tablename__ = 'student_nudges'
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    student_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Nudge content fields
    nudge_type = Column(Enum(NudgeType), nullable=False)
    message = Column(Text, nullable=False)
    
    # Delivery settings fields
    channel = Column(Enum(Channel), nullable=False, default=Channel.IN_APP)
    audio_url = Column(String(500), nullable=True)
    priority = Column(Enum(Priority), nullable=False, default=Priority.NORMAL)
    
    # Delivery tracking field
    status = Column(Enum(NudgeStatus), nullable=False, default=NudgeStatus.SENT)
    
    # Timestamp fields
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Table arguments with indexes and constraints
    __table_args__ = (
        # Composite indexes for optimized queries
        Index('idx_student_nudges_tenant_student', 'tenant_id', 'student_id'),
        Index('idx_student_nudges_student_type', 'student_id', 'nudge_type'),
        Index('idx_student_nudges_status_priority', 'status', 'priority'),
        Index('idx_student_nudges_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_student_nudges_channel_status', 'channel', 'status'),
        
        # Single column indexes for frequent queries
        Index('idx_student_nudges_nudge_type', 'nudge_type'),
        Index('idx_student_nudges_sent_at', 'sent_at'),
        Index('idx_student_nudges_read_at', 'read_at'),
        
        # Extend existing table configuration
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f"<StudentNudge(id={self.id}, student_id={self.student_id}, nudge_type={self.nudge_type.value}, status={self.status.value})>"
    
    def to_dict(self):
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'student_id': str(self.student_id),
            'nudge_type': self.nudge_type.value,
            'message': self.message,
            'channel': self.channel.value,
            'audio_url': self.audio_url,
            'priority': self.priority.value,
            'status': self.status.value,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_nudge(cls, tenant_id, student_id, nudge_type, message, 
                    channel=Channel.IN_APP, priority=Priority.NORMAL, audio_url=None):
        """Factory method to create a new student nudge"""
        return cls(
            tenant_id=tenant_id,
            student_id=student_id,
            nudge_type=nudge_type,
            message=message,
            channel=channel,
            priority=priority,
            audio_url=audio_url
        )
    
    def mark_as_sent(self):
        """Mark the nudge as sent and update timestamp"""
        self.status = NudgeStatus.SENT
        self.sent_at = func.now()
    
    def mark_as_delivered(self):
        """Mark the nudge as delivered"""
        self.status = NudgeStatus.DELIVERED
    
    def mark_as_read(self):
        """Mark the nudge as read and update timestamp"""
        self.status = NudgeStatus.READ
        self.read_at = func.now()
    
    def mark_as_failed(self):
        """Mark the nudge as failed"""
        self.status = NudgeStatus.FAILED