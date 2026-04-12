"""
Analytics events model for tracking and reporting
"""
import enum
from sqlalchemy import Column, String, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel

class EventType(enum.Enum):
    """Types of analytics events"""
    # User events
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_REGISTRATION = "USER_REGISTRATION"
    
    # Lead events
    LEAD_CREATED = "LEAD_CREATED"
    LEAD_UPDATED = "LEAD_UPDATED"
    LEAD_CONVERTED = "LEAD_CONVERTED"
    LEAD_QUALIFIED = "LEAD_QUALIFIED"
    LEAD_CONTEXT_MERGED = "LEAD_CONTEXT_MERGED"
    LEAD_ASSIGNED = "LEAD_ASSIGNED"
    LEAD_DELETED = "LEAD_DELETED"
    LEAD_STATUS_CHANGED = "LEAD_STATUS_CHANGED"
    
    # Chatbot events
    CHATBOT_SESSION_START = "CHATBOT_SESSION_START"
    CHATBOT_SESSION_END = "CHATBOT_SESSION_END"
    CHATBOT_INTENT_DETECTED = "CHATBOT_INTENT_DETECTED"
    CHATBOT_ESCALATION = "CHATBOT_ESCALATION"
    
    # Communication events
    CALL_INITIATED = "CALL_INITIATED"
    CALL_COMPLETED = "CALL_COMPLETED"
    CALL_TRIGGERED = "CALL_TRIGGERED"
    CALL_UPDATED = "CALL_UPDATED"
    EMAIL_SENT = "EMAIL_SENT"
    SMS_SENT = "SMS_SENT"
    
    # Demo events
    DEMO_SCHEDULED = "DEMO_SCHEDULED"
    DEMO_ATTENDED = "DEMO_ATTENDED"
    DEMO_NO_SHOW = "DEMO_NO_SHOW"
    DEMO_RESCHEDULED = "DEMO_RESCHEDULED"
    DEMO_CANCELLED = "DEMO_CANCELLED"
    DEMO_REMINDER_SENT = "DEMO_REMINDER_SENT"
    
    # Enrollment events
    COURSE_ENROLLED = "COURSE_ENROLLED"
    ENROLLMENT_CREATED = "ENROLLMENT_CREATED"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    
    # Student events
    STUDENT_LOGIN = "STUDENT_LOGIN"
    MODULE_COMPLETED = "MODULE_COMPLETED"
    ASSIGNMENT_SUBMITTED = "ASSIGNMENT_SUBMITTED"
    QUIZ_COMPLETED = "QUIZ_COMPLETED"
    
    # Teaching events
    QUESTION_ASKED = "QUESTION_ASKED"
    ANSWER_PROVIDED = "ANSWER_PROVIDED"
    CONCEPT_EXPLAINED = "CONCEPT_EXPLAINED"
    
    # System events
    API_REQUEST = "API_REQUEST"
    ERROR_OCCURRED = "ERROR_OCCURRED"
    RATE_LIMIT_HIT = "RATE_LIMIT_HIT"
    
    # Business events
    REVENUE_GENERATED = "REVENUE_GENERATED"
    REFUND_PROCESSED = "REFUND_PROCESSED"
    SUBSCRIPTION_UPGRADED = "SUBSCRIPTION_UPGRADED"
    SUBSCRIPTION_DOWNGRADED = "SUBSCRIPTION_DOWNGRADED"

class AnalyticsEvent(BaseModel):
    """Analytics event model for comprehensive tracking"""
    __tablename__ = 'analytics_events'
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Event classification
    event_type = Column(
        Enum(EventType), 
        nullable=False, 
        index=True
    )
    entity_type = Column(String(50), nullable=True, index=True)  # lead, user, student, etc.
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # ID of related entity
    
    # Event context
    session_id = Column(String(255), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Event data
    event_metadata = Column(JSONB, nullable=True)  # Flexible event-specific data
    properties = Column(JSONB, nullable=True)  # Additional properties
    metrics = Column(JSONB, nullable=True)  # Numerical metrics
    
    # Event source
    source = Column(String(100), nullable=True, index=True)  # web, api, mobile, system
    channel = Column(String(100), nullable=True)  # specific channel within source
    
    # Geographic information
    country = Column(String(2), nullable=True)  # ISO country code
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Performance metrics
    duration_ms = Column(String(20), nullable=True)  # Event duration in milliseconds
    response_time_ms = Column(String(20), nullable=True)  # Response time if applicable
    
    # Revenue tracking (for revenue events)
    revenue_amount = Column(String(20), nullable=True)  # Stored as string for precision
    currency = Column(String(3), nullable=True)
    
    # Campaign tracking
    campaign_id = Column(String(100), nullable=True)
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    utm_term = Column(String(100), nullable=True)
    utm_content = Column(String(100), nullable=True)
    
    # Error tracking (for error events)
    error_code = Column(String(50), nullable=True)
    error_message = Column(String(1000), nullable=True)
    stack_trace = Column(String(5000), nullable=True)
    
    # A/B testing
    experiment_id = Column(String(100), nullable=True)
    variant_id = Column(String(100), nullable=True)
    
    # Data quality
    is_test_data = Column(String(10), default="false", index=True)
    data_quality_score = Column(String(10), nullable=True)  # 0-100
    
    # Relationships
    tenant = relationship("Tenant", back_populates="analytics_events")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_analytics_tenant_event_type', 'tenant_id', 'event_type'),
        Index('idx_analytics_entity', 'entity_type', 'entity_id'),
        Index('idx_analytics_session', 'session_id', 'created_at'),
        Index('idx_analytics_user', 'user_id', 'created_at'),
        Index('idx_analytics_source_channel', 'source', 'channel'),
        Index('idx_analytics_revenue', 'revenue_amount', 'currency'),
        Index('idx_analytics_campaign', 'campaign_id', 'utm_source'),
        Index('idx_analytics_errors', 'error_code', 'created_at'),
        Index('idx_analytics_test_data', 'is_test_data'),
        Index('idx_analytics_created_at', 'created_at'),  # Time-series queries
    )
