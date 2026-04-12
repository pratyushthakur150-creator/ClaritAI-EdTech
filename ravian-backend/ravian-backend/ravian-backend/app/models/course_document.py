"""
CourseDocument model for Teaching Assistant content indexing.
Stores metadata for PDFs, videos, YouTube, PPTX, etc. indexed into ChromaDB.
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from .base import Base


class CourseDocument(Base):
    """Model for course documents indexed into ChromaDB (PDF, video, YouTube, PPTX, etc.)"""
    __tablename__ = 'course_documents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    course_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False)  # pdf, video, youtube, pptx, text, markdown
    original_url = Column(String(2000), nullable=True)  # for YouTube URLs
    status = Column(String(20), nullable=False, default='uploading')
    file_path = Column(String(1000), nullable=True)
    file_size = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    vector_count = Column(Integer, default=0)
    chroma_collection = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSONB, default=list)
    doc_metadata = Column(JSONB, default=dict)
    error_message = Column(Text, nullable=True)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False)
    last_updated = Column(DateTime(timezone=True), onupdate=func.current_timestamp(), nullable=True)

    __table_args__ = (
        Index('idx_cd_tenant_course', 'tenant_id', 'course_id'),
        Index('idx_cd_status', 'status'),
        Index('idx_cd_type', 'document_type'),
        {'extend_existing': True}
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'course_id': str(self.course_id),
            'title': self.title,
            'document_type': self.document_type,
            'original_url': self.original_url,
            'status': self.status,
            'file_size': self.file_size or 0,
            'chunk_count': self.chunk_count or 0,
            'vector_count': self.vector_count or 0,
            'chroma_collection': self.chroma_collection,
            'description': self.description,
            'tags': self.tags or [],
            'doc_metadata': self.doc_metadata or {},
            'error_message': self.error_message,
            'upload_timestamp': self.upload_timestamp.isoformat() if self.upload_timestamp else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }
