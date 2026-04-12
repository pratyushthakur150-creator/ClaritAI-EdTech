"""
Database models package - imports all models for easy access
"""

# Import base model
from .base import Base, BaseModel

# Import all models
from .tenant import Tenant, User, SubscriptionPlan, UserRole
from .lead import Lead, ChatbotSession, LeadStatus, LeadSource, UrgencyLevel
from .call import CallLog, Demo, CallDirection, CallOutcome, SentimentScore, DemoOutcome
from .enrollment import Enrollment, Student, PaymentStatus, RiskLevel
from .teaching import Course, TeachingInteraction, ConfusionLevel, InteractionType
from .analytics import AnalyticsEvent, EventType
from .course_module import CourseModule
from .student_interaction import StudentInteraction
from .student_nudge import StudentNudge
from .voice_conversation import VoiceConversation
from .course_document import CourseDocument

# Export all models and enums for easy import
__all__ = [
    # Base
    "Base",
    "BaseModel",
    
    # Tenant models
    "Tenant",
    "User",
    "SubscriptionPlan",
    "UserRole",
    
    # Lead models
    "Lead",
    "ChatbotSession", 
    "LeadStatus",
    "LeadSource",
    "UrgencyLevel",
    
    # Call models
    "CallLog",
    "Demo",
    "CallDirection",
    "CallOutcome", 
    "SentimentScore",
    "DemoOutcome",
    
    # Enrollment models
    "Enrollment",
    "Student",
    "PaymentStatus",
    "RiskLevel",
    
    # Teaching models
    "Course",
    "TeachingInteraction",
    "ConfusionLevel",
    "InteractionType",
    
    # Analytics models
    "AnalyticsEvent",
    "EventType",
    
    # Teaching Assistant models
    "CourseModule",
    "StudentInteraction",
    "StudentNudge",
    "VoiceConversation",
    "CourseDocument",
]
