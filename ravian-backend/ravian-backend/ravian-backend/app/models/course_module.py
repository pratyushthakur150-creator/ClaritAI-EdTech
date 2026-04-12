"""
SQLAlchemy model for CourseModule - represents hierarchical course module structure.
Used by the Teaching Assistant module for organizing course content and 
confusion heatmap visualization.
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from .base import Base

class CourseModule(Base):
    """
    SQLAlchemy model for course modules - hierarchical structure of course content.
    
    This model represents individual modules within courses and is used by the 
    Teaching Assistant module to:
    - Organize course content hierarchically
    - Generate confusion heatmaps by module
    - Track student interactions at module level
    - Enable module-specific nudges and interventions
    """
    
    __tablename__ = 'course_modules'
    
    # Primary identifier fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    course_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Module detail fields
    name = Column(String(255), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        # Indexes for performance optimization
        Index('idx_course_modules_tenant_id', 'tenant_id'),
        Index('idx_course_modules_course_id', 'course_id'),
        Index('idx_course_modules_order_index', 'order_index'),
        Index('idx_course_modules_name', 'name'),
        Index('idx_course_modules_created_at', 'created_at'),
        
        # Composite indexes for common query patterns
        Index('idx_course_modules_tenant_course', 'tenant_id', 'course_id'),
        Index('idx_course_modules_course_order', 'course_id', 'order_index'),
        Index('idx_course_modules_tenant_created', 'tenant_id', 'created_at'),
        
        # Unique constraint for module ordering within course
        Index('idx_course_modules_course_order_unique', 'course_id', 'order_index', unique=True),
        
        # Allow model extension
        {'extend_existing': True}
    )
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'course_id': str(self.course_id),
            'name': self.name,
            'description': self.description,
            'order_index': self.order_index,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_module(cls, tenant_id, course_id, name, description=None, order_index=0):
        """
        Create a new course module.
        
        Args:
            tenant_id: UUID of the tenant
            course_id: UUID of the course
            name: Module name
            description: Optional module description
            order_index: Sequential order within course
            
        Returns:
            CourseModule: New module instance
        """
        return cls(
            tenant_id=tenant_id,
            course_id=course_id,
            name=name,
            description=description,
            order_index=order_index
        )
    
    def update_order(self, new_order_index):
        """Update the module's order index."""
        self.order_index = new_order_index
        self.updated_at = func.now()
    
    def __repr__(self):
        return f"<CourseModule(id={self.id}, name='{self.name}', course_id={self.course_id}, order={self.order_index})>"