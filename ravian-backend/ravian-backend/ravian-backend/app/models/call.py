"""
Call logs and Demo models for communication tracking
"""
import enum
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum, DateTime, Numeric, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel

class CallDirection(enum.Enum):
    """Call direction types"""
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"

class CallOutcome(enum.Enum):
    """Call outcome classifications"""
    CONNECTED = "CONNECTED"
    NO_ANSWER = "NO_ANSWER"
    VOICEMAIL = "VOICEMAIL"
    BUSY = "BUSY"
    FAILED = "FAILED"
    SCHEDULED_CALLBACK = "SCHEDULED_CALLBACK"

class SentimentScore(enum.Enum):
    """Sentiment analysis results"""
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"

class DemoOutcome(enum.Enum):
    """Demo session outcomes"""
    ENROLLED = "enrolled"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    RESCHEDULE = "reschedule"
    NO_SHOW = "no_show"

class CallLog(BaseModel):
    """Call log model for tracking communications"""
    __tablename__ = 'call_logs'
    
    # Multi-tenant support
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey('leads.id'), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Call details
    call_direction = Column(Enum(CallDirection), nullable=False, index=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    phone_number = Column(String(20), nullable=True)
    
    # Content analysis
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    sentiment = Column(Enum(SentimentScore), nullable=True, index=True)
    outcome = Column(Enum(CallOutcome), nullable=False, index=True)
    
    # Media and costs
    recording_url = Column(String(500), nullable=True)
    cost = Column(Numeric(10, 4), nullable=True)  # Cost in currency units
    
    # Additional context
    notes = Column(Text, nullable=True)
    follow_up_required = Column(String(10), default="false")
    next_action = Column(String(255), nullable=True)
    
    # AI analysis
    key_topics = Column(JSONB, nullable=True)  # Topics discussed
    questions_asked = Column(JSONB, nullable=True)  # Questions from lead
    objections = Column(JSONB, nullable=True)  # Objections raised
    
    # Relationships
    tenant = relationship("Tenant")
    lead = relationship("Lead", back_populates="call_logs")
    agent = relationship("User", foreign_keys=[agent_id])
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_call_tenant_id', 'tenant_id'),
        Index('idx_call_lead_direction', 'lead_id', 'call_direction'),
        Index('idx_call_outcome_sentiment', 'outcome', 'sentiment'),
        Index('idx_call_follow_up', 'follow_up_required', 'created_at'),
        Index('idx_call_cost', 'cost'),
    )

class Demo(BaseModel):
    """Demo session scheduling and tracking (multi-tenant, mentor + course aware)."""
    __tablename__ = 'demos'

    # Core foreign keys
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey('leads.id'), nullable=False, index=True)
    mentor_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id'), nullable=True, index=True)

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, default=60)
    timezone = Column(String(50), nullable=True)

    # Attendance
    completed = Column(Boolean, default=False, nullable=False, index=True)
    attended = Column(Boolean, nullable=True, default=None, index=True)
    attendee_count = Column(Integer, default=1)

    # Outcome and interest
    outcome = Column(String(50), nullable=True, index=True)  # e.g. enrolled, no_show, cancelled
    interest_level = Column(Integer, nullable=True)  # 1-10 scale

    # Content
    notes = Column(Text, nullable=True)
    courses_demonstrated = Column(JSONB, nullable=True)  # List of courses shown
    questions_asked = Column(JSONB, nullable=True)
    objections = Column(JSONB, nullable=True)

    # Follow-up
    follow_up_scheduled = Column(DateTime(timezone=True), nullable=True)
    next_steps = Column(Text, nullable=True)

    # Technical details
    platform = Column(String(50), nullable=True)  # Zoom, Teams, etc.
    meeting_link = Column(String(500), nullable=True)
    recording_url = Column(String(500), nullable=True)
    google_event_id = Column(String(255), nullable=True)  # Google Calendar event ID

    # Operational
    reschedule_count = Column(Integer, default=0, nullable=False)

    # Relationships
    lead = relationship("Lead", back_populates="demos")
    mentor = relationship("User", foreign_keys=[mentor_id])
    course = relationship("Course", back_populates="demos")
    tenant = relationship("Tenant")

    # Indexes for performance
    __table_args__ = (
        Index('idx_demo_tenant_lead', 'tenant_id', 'lead_id'),
        Index('idx_demo_scheduled_at', 'scheduled_at'),
        Index('idx_demo_follow_up', 'follow_up_scheduled'),
    )
