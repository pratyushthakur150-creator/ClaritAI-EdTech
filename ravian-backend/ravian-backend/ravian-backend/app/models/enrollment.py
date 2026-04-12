"""
Enrollment and Student models for course enrollment tracking
"""
import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, DateTime, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel

class PaymentStatus(enum.Enum):
    """Payment status for enrollments"""
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"

class RiskLevel(enum.Enum):
    """Student risk levels for dropout prediction"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Enrollment(BaseModel):
    """Course enrollment model"""
    __tablename__ = 'enrollments'
    
    # Multi-tenant support
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    lead_id = Column(UUID(as_uuid=True), ForeignKey('leads.id'), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id'), nullable=False, index=True)
    batch_id = Column(String(100), nullable=True, index=True)
    
    # Enrollment details
    enrolled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    expected_completion_date = Column(DateTime(timezone=True), nullable=True)
    actual_completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # Payment information
    payment_status = Column(
        Enum(PaymentStatus), 
        nullable=False, 
        default=PaymentStatus.PENDING,
        index=True
    )
    total_amount = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    
    # Payment details
    payment_plan = Column(String(50), nullable=True)  # full, installment, etc.
    installments_total = Column(Integer, nullable=True)
    installments_paid = Column(Integer, default=0)
    
    # Enrollment context
    discount_applied = Column(Numeric(5, 2), nullable=True)  # Percentage
    coupon_code = Column(String(50), nullable=True)
    referral_source = Column(String(100), nullable=True)
    
    # Additional information
    enrollment_notes = Column(String(1000), nullable=True)
    special_requirements = Column(JSONB, nullable=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    student = relationship("Student", back_populates="enrollment", uselist=False, cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_enrollment_tenant_lead', 'tenant_id', 'lead_id'),
        Index('idx_enrollment_lead_course', 'lead_id', 'course_id'),
        Index('idx_enrollment_payment_status', 'payment_status'),
        Index('idx_enrollment_batch', 'batch_id', 'enrolled_at'),
        Index('idx_enrollment_amount', 'total_amount', 'amount_paid'),
        Index('idx_enrollment_dates', 'enrolled_at', 'start_date'),
    )

class Student(BaseModel):
    """Student model for enrolled learners"""
    __tablename__ = 'students'
    
    lead_id = Column(UUID(as_uuid=True), ForeignKey('leads.id'), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey('enrollments.id'), nullable=False, index=True)
    
    # External system integration
    lms_user_id = Column(String(100), nullable=True, index=True)  # Learning Management System ID
    student_id = Column(String(50), nullable=True, index=True)  # Internal student ID
    
    # Engagement metrics
    engagement_score = Column(Integer, default=0, index=True)  # 0-100
    total_study_hours = Column(Numeric(8, 2), default=0)
    assignments_completed = Column(Integer, default=0)
    assignments_total = Column(Integer, default=0)
    
    # Progress tracking
    modules_completed = Column(Integer, default=0)
    modules_total = Column(Integer, default=0)
    completion_percentage = Column(Numeric(5, 2), default=0)  # 0-100
    current_module = Column(String(100), nullable=True)
    
    # Risk assessment
    risk_score = Column(Integer, default=0, index=True)  # 0-100 (100 = high risk)
    risk_level = Column(
        Enum(RiskLevel), 
        default=RiskLevel.LOW,
        index=True
    )
    risk_factors = Column(JSONB, nullable=True)  # Specific risk indicators
    
    # Activity tracking
    last_active = Column(DateTime(timezone=True), nullable=True, index=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_streak = Column(Integer, default=0)
    total_logins = Column(Integer, default=0)
    
    # Performance metrics
    average_assignment_score = Column(Numeric(5, 2), nullable=True)  # 0-100
    quiz_scores = Column(JSONB, nullable=True)  # Array of quiz results
    project_scores = Column(JSONB, nullable=True)  # Project evaluation scores
    
    # Communication preferences
    preferred_contact_method = Column(String(50), nullable=True)
    communication_frequency = Column(String(50), nullable=True)  # daily, weekly, monthly
    
    # Support and mentoring
    mentor_assigned = Column(UUID(as_uuid=True), nullable=True)
    support_tickets_count = Column(Integer, default=0)
    mentoring_sessions_count = Column(Integer, default=0)
    
    # Additional context
    learning_goals = Column(JSONB, nullable=True)
    career_objectives = Column(String(500), nullable=True)
    feedback_provided = Column(JSONB, nullable=True)
    
    # Relationships
    lead = relationship("Lead")
    tenant = relationship("Tenant", back_populates="students")
    enrollment = relationship("Enrollment", back_populates="student")
    teaching_interactions = relationship("TeachingInteraction", back_populates="student", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_student_tenant_engagement', 'tenant_id', 'engagement_score'),
        Index('idx_student_risk_level', 'risk_level', 'risk_score'),
        Index('idx_student_last_active', 'last_active'),
        Index('idx_student_completion', 'completion_percentage'),
        Index('idx_student_lms_id', 'lms_user_id'),
        Index('idx_student_enrollment', 'enrollment_id'),
    )
