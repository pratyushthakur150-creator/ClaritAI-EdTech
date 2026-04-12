"""
Tenant and User models for multi-tenant architecture
"""
import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, Text, Index, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel

class SubscriptionPlan(enum.Enum):
    """Subscription plan levels"""
    STARTER = "starter"
    GROWTH = "growth" 
    ENTERPRISE = "enterprise"
    ADMIN = "admin"

class UserRole(enum.Enum):
    """User role types - values must match PostgreSQL enum userrole ('ADMIN', 'MENTOR', 'VIEWER')"""
    ADMIN = "ADMIN"
    MENTOR = "MENTOR"
    VIEWER = "VIEWER"

class Tenant(BaseModel):
    """Tenant model for multi-tenancy"""
    __tablename__ = 'tenants'
    
    name = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    branding = Column(JSONB, nullable=True)  # Logo, colors, themes
    subscription_plan = Column(
        Enum(SubscriptionPlan), 
        nullable=False, 
        default=SubscriptionPlan.STARTER,
        index=True
    )
    credits_remaining = Column(Integer, default=1000, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="tenant", cascade="all, delete-orphan")
    chatbot_sessions = relationship("ChatbotSession", back_populates="tenant", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="tenant", cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="tenant", cascade="all, delete-orphan")
    analytics_events = relationship("AnalyticsEvent", back_populates="tenant", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_tenant_plan_credits', 'subscription_plan', 'credits_remaining'),
    )

class User(BaseModel):
    """User model with role-based access"""
    __tablename__ = 'users'
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(
        Enum(UserRole), 
        nullable=False, 
        default=UserRole.VIEWER,
        index=True
    )
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    assigned_leads = relationship("Lead", foreign_keys="Lead.assigned_to", back_populates="assigned_user")
    created_leads = relationship("Lead", foreign_keys="Lead.created_by", back_populates="created_by_user")
    updated_leads = relationship("Lead", foreign_keys="Lead.updated_by", back_populates="updated_by_user")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_tenant_email', 'tenant_id', 'email'),
        Index('idx_user_tenant_role', 'tenant_id', 'role'),
    )
