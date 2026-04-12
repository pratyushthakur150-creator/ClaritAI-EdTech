"""
Pydantic schemas for conversation context management.
This module defines all the data models for handling conversation contexts,
including messages, context creation, responses, and usage statistics.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class ContextType(str, Enum):
    """Supported conversation context types"""
    CHATBOT = "chatbot"
    VOICE_AGENT = "voice_agent"
    TEACHING_ASSISTANT = "teaching_assistant"


class MessageRole(str, Enum):
    """Supported message roles in conversations"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageCreate(BaseModel):
    """Schema for creating a message within a context"""
    role: MessageRole
    content: str = Field(..., min_length=1, max_length=10000)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class MessageResponse(BaseModel):
    """Schema for message response"""
    role: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True


class ContextCreateRequest(BaseModel):
    """Request schema for creating a new conversation context"""
    user_id: UUID
    context_type: ContextType = Field(default=ContextType.CHATBOT)
    initial_messages: Optional[List[MessageCreate]] = Field(default=None, max_items=10)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('initial_messages')
    def validate_initial_messages(cls, v):
        if v and len(v) > 10:
            raise ValueError('Cannot have more than 10 initial messages')
        return v

    class Config:
        use_enum_values = True


class ContextResponse(BaseModel):
    """Response schema for conversation context details"""
    context_id: UUID
    user_id: UUID
    tenant_id: UUID
    context_type: str
    messages: List[Dict[str, Any]]
    message_count: int
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AddMessageRequest(BaseModel):
    """Request schema for adding a message to existing context"""
    context_id: UUID
    role: MessageRole
    content: str = Field(..., min_length=1, max_length=10000)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Message content cannot be empty')
        return v

    class Config:
        use_enum_values = True


class AddMessageResponse(BaseModel):
    """Response schema for message addition"""
    message_id: str
    context_id: UUID
    role: str
    content: str
    timestamp: datetime
    context_message_count: int

    class Config:
        from_attributes = True


class ContextListItem(BaseModel):
    """Schema for context in list responses"""
    context_id: UUID
    user_id: UUID
    context_type: str
    message_count: int
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserContextsResponse(BaseModel):
    """Response schema for user's contexts list"""
    contexts: List[ContextListItem]
    total_count: int
    user_id: UUID

    class Config:
        from_attributes = True


class ContextStatsResponse(BaseModel):
    """Response schema for context usage statistics"""
    total_contexts: int
    total_messages: int
    contexts_by_type: Dict[str, int]
    messages_by_role: Dict[str, int]
    active_contexts_last_24h: int
    active_contexts_last_7d: int
    avg_messages_per_context: float
    avg_context_duration_hours: float
    date_from: datetime
    date_to: datetime

    class Config:
        from_attributes = True


class ContextDeleteResponse(BaseModel):
    """Response schema for context deletion"""
    success: bool
    context_id: UUID
    message_count: int
    deleted_at: datetime

    class Config:
        from_attributes = True
