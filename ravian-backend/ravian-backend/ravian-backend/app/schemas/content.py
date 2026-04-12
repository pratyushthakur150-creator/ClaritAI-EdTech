"""
Content Management Schemas for Teaching Assistant Module.

Pydantic models for document upload, listing, and indexing responses.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Supported document types for content indexing."""
    PDF = "pdf"
    TEXT = "text"
    VIDEO_TRANSCRIPT = "video_transcript"
    SLIDES = "slides"
    PPTX = "pptx"
    MARKDOWN = "markdown"
    VIDEO = "video"
    YOUTUBE = "youtube"
    IMAGE = "image"


class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"
    DELETED = "deleted"


class DocumentIndexResponse(BaseModel):
    """Response schema for document index/upload."""
    document_id: str
    title: str
    document_type: str
    status: str
    course_id: str
    tenant_id: str
    upload_timestamp: datetime
    file_size: int = 0
    chunk_count: int = 0
    vector_count: int = 0
    processing_time: Optional[float] = None
    chroma_collection: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentMetadata(BaseModel):
    """Metadata for a single document in list response."""
    document_id: str
    title: str
    document_type: str
    status: str
    course_id: str
    file_size: int = 0
    chunk_count: int = 0
    upload_timestamp: datetime
    last_updated: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    error_message: Optional[str] = None
    chroma_collection: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Response schema for document list."""
    course_id: str
    tenant_id: str
    total_documents: int
    documents: List[DocumentMetadata]
    request_timestamp: datetime


class BatchDocumentIndexResponse(BaseModel):
    """Response schema for batch document upload."""
    total_files: int
    successful: int
    failed: int
    results: List[DocumentIndexResponse] = Field(default_factory=list)
    errors: List[Dict[str, str]] = Field(default_factory=list)
