"""
Teaching interactions and Course models for educational content
"""
import enum
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from .base import BaseModel

class ConfusionLevel(enum.Enum):
    """Student confusion levels in teaching interactions"""
    CLEAR = "clear"
    SLIGHT = "slight"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

class InteractionType(enum.Enum):
    """Types of teaching interactions"""
    QUESTION = "question"
    CLARIFICATION = "clarification"
    ASSIGNMENT_HELP = "assignment_help"
    CONCEPT_EXPLANATION = "concept_explanation"
    FEEDBACK_REQUEST = "feedback_request"
    TECHNICAL_ISSUE = "technical_issue"
    OTHER = "other"

class Course(BaseModel):
    """Course model for educational offerings"""
    __tablename__ = 'courses'
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Course basic information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    course_code = Column(String(50), nullable=True, unique=True, index=True)
    
    # Course structure
    syllabus = Column(JSONB, nullable=True)  # Detailed syllabus with modules
    modules = Column(JSONB, nullable=True)  # Course modules structure
    prerequisites = Column(ARRAY(String), nullable=True)
    learning_outcomes = Column(JSONB, nullable=True)
    
    # Course metadata
    difficulty_level = Column(String(50), nullable=True)  # Beginner, Intermediate, Advanced
    duration_weeks = Column(Integer, nullable=True)
    total_hours = Column(Integer, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    tags = Column(ARRAY(String), nullable=True)
    
    # Enrollment information
    max_students = Column(Integer, nullable=True)
    price = Column(String(20), nullable=True)  # Stored as string for flexibility
    currency = Column(String(3), default="USD")
    
    # Content indexing
    indexed = Column(String(10), default="false", index=True)  # For search indexing
    content_vector = Column(JSONB, nullable=True)  # Vector embeddings for AI
    
    # Course status
    is_active = Column(String(10), default="true", index=True)
    is_published = Column(String(10), default="false", index=True)
    
    # Analytics
    enrollment_count = Column(Integer, default=0)
    completion_rate = Column(Integer, default=0)  # Percentage
    average_rating = Column(Integer, default=0)  # 0-100 scale
    
    # Relationships
    tenant = relationship("Tenant", back_populates="courses")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    teaching_interactions = relationship("TeachingInteraction", back_populates="course", cascade="all, delete-orphan")
    demos = relationship("Demo", back_populates="course", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_course_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_course_category_published', 'category', 'is_published'),
        Index('idx_course_indexed', 'indexed'),
        Index('idx_course_enrollment_count', 'enrollment_count'),
    )

class TeachingInteraction(BaseModel):
    """Teaching interaction model for student-teacher communications"""
    __tablename__ = 'teaching_interactions'
    
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id'), nullable=False, index=True)
    
    # Content structure
    module_id = Column(String(100), nullable=True, index=True)  # Course module identifier
    lesson_id = Column(String(100), nullable=True)  # Specific lesson
    topic = Column(String(255), nullable=True, index=True)
    
    # Interaction content
    query = Column(Text, nullable=False)  # Student's question/input
    response = Column(Text, nullable=True)  # System/teacher response
    interaction_type = Column(
        Enum(InteractionType), 
        nullable=False, 
        default=InteractionType.QUESTION,
        index=True
    )
    
    # Assessment
    confusion_level = Column(
        Enum(ConfusionLevel), 
        nullable=False, 
        default=ConfusionLevel.CLEAR,
        index=True
    )
    difficulty_rating = Column(Integer, nullable=True)  # 1-10 scale
    satisfaction_rating = Column(Integer, nullable=True)  # 1-10 scale
    
    # Context and analysis
    context = Column(JSONB, nullable=True)  # Additional context
    concepts_discussed = Column(ARRAY(String), nullable=True)
    keywords = Column(ARRAY(String), nullable=True)
    
    # AI analysis
    intent_detected = Column(String(100), nullable=True)
    entities_extracted = Column(JSONB, nullable=True)
    sentiment_score = Column(Integer, nullable=True)  # -100 to 100
    
    # Resolution
    resolved = Column(String(10), default="false", index=True)
    resolution_time_minutes = Column(Integer, nullable=True)
    follow_up_required = Column(String(10), default="false")
    
    # Teaching effectiveness
    helpful_rating = Column(Integer, nullable=True)  # 1-10 scale
    clarity_rating = Column(Integer, nullable=True)  # 1-10 scale
    
    # Additional metadata
    interaction_source = Column(String(50), nullable=True)  # chat, email, forum, etc.
    teacher_id = Column(UUID(as_uuid=True), nullable=True)  # If human teacher involved
    response_method = Column(String(50), nullable=True)  # AI, human, hybrid
    
    # Relationships
    student = relationship("Student", back_populates="teaching_interactions")
    course = relationship("Course", back_populates="teaching_interactions")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_teaching_student_course', 'student_id', 'course_id'),
        Index('idx_teaching_module_topic', 'module_id', 'topic'),
        Index('idx_teaching_confusion_level', 'confusion_level'),
        Index('idx_teaching_resolved', 'resolved', 'created_at'),
        Index('idx_teaching_interaction_type', 'interaction_type'),
        Index('idx_teaching_follow_up', 'follow_up_required'),
    )
