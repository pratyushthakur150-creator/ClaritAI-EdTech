"""
Lead and ChatbotSession models for lead management
"""
import enum
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from .base import BaseModel

class LeadStatus(enum.Enum):
    """Lead status progression - values match PostgreSQL leadstatus enum"""
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    DEMO_SCHEDULED = "DEMO_SCHEDULED"
    DEMO_COMPLETED = "DEMO_COMPLETED"
    ENROLLED = "ENROLLED"
    LOST = "LOST"
    NURTURING = "NURTURING"


class LeadSource(enum.Enum):
    """Lead acquisition sources - values match PostgreSQL leadsource enum"""
    WEBSITE = "WEBSITE"
    CHATBOT = "CHATBOT"
    REFERRAL = "REFERRAL"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    ADVERTISING = "ADVERTISING"
    EMAIL_CAMPAIGN = "EMAIL_CAMPAIGN"
    DIRECT = "DIRECT"
    OTHER = "OTHER"


class UrgencyLevel(enum.Enum):
    """Lead urgency levels - values match PostgreSQL urgencylevel enum"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Lead(BaseModel):
    """Lead model for prospect management"""
    __tablename__ = 'leads'
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    
    # Contact information
    name = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    
    # Lead classification
    source = Column(Enum(LeadSource), nullable=False, index=True)
    status = Column(
        Enum(LeadStatus), 
        nullable=False, 
        default=LeadStatus.NEW,
        index=True
    )
    intent = Column(Text, nullable=True)
    interested_courses = Column(ARRAY(String), nullable=True)
    urgency = Column(
        Enum(UrgencyLevel), 
        nullable=False, 
        default=UrgencyLevel.MEDIUM,
        index=True
    )
    
    # Context and notes
    chatbot_context = Column(JSONB, nullable=True)  # Chatbot conversation summary
    chatbot_session_id = Column(UUID(as_uuid=True), ForeignKey('chatbot_sessions.id'), nullable=True, index=True)  # Link to chatbot session
    notes = Column(Text, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    
    # Scoring
    engagement_score = Column(Integer, default=0)
    conversion_probability = Column(Integer, default=0)  # 0-100
    
    # Relationships
    tenant = relationship("Tenant", back_populates="leads")
    assigned_user = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_leads")
    created_by_user = relationship("User", foreign_keys=[created_by], back_populates="created_leads")
    updated_by_user = relationship("User", foreign_keys=[updated_by], back_populates="updated_leads")
    
    # All chatbot sessions where this lead is referenced (one-to-many via ChatbotSession.lead_id)
    chatbot_sessions = relationship(
        "ChatbotSession",
        primaryjoin="Lead.id == ChatbotSession.lead_id",
        foreign_keys="ChatbotSession.lead_id",
        back_populates="lead",
        cascade="all, delete-orphan"
    )
    
    # Specific chatbot session that created this lead (one-to-one via Lead.chatbot_session_id)
    chatbot_session = relationship(
        "ChatbotSession",
        foreign_keys=[chatbot_session_id],
        primaryjoin="Lead.chatbot_session_id == ChatbotSession.id",
        uselist=False,
        viewonly=True  # Read-only to prevent circular dependencies
    )
    
    call_logs = relationship("CallLog", back_populates="lead", cascade="all, delete-orphan")
    demos = relationship("Demo", back_populates="lead", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="lead", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_lead_tenant_status', 'tenant_id', 'status'),
        Index('idx_lead_tenant_source', 'tenant_id', 'source'),
        Index('idx_lead_assigned_status', 'assigned_to', 'status'),
        Index('idx_lead_email_phone', 'email', 'phone'),
        Index('idx_lead_engagement_score', 'engagement_score'),
    )

class ChatbotSession(BaseModel):
    """Chatbot conversation sessions"""
    __tablename__ = 'chatbot_sessions'
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey('leads.id'), nullable=True, index=True)
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Conversation data
    conversation = Column(JSONB, nullable=False)  # Full conversation history
    summary = Column(Text, nullable=True)
    intent_detected = Column(String(255), nullable=True)
    entities_extracted = Column(JSONB, nullable=True)  # NLP entities
    
    # Metrics
    engagement_score = Column(Integer, default=0)
    message_count = Column(Integer, default=0)
    duration_seconds = Column(Integer, nullable=True)
    lead_captured = Column(String(10), default="false")
    
    # Session info
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    referrer = Column(Text, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="chatbot_sessions")
    # Explicitly use lead_id foreign key to avoid ambiguity with Lead.chatbot_session_id
    lead = relationship(
        "Lead",
        foreign_keys=[lead_id],
        back_populates="chatbot_sessions"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_chatbot_session_tenant', 'tenant_id', 'created_at'),
        Index('idx_chatbot_session_lead', 'lead_id'),
        Index('idx_chatbot_engagement', 'engagement_score'),
        Index('idx_chatbot_lead_captured', 'lead_captured'),
    )
