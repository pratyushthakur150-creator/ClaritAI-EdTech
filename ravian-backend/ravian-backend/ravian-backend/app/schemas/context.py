"""
Pydantic schemas for conversation context management.

This module defines all the data models for handling conversation contexts,
including messages, context creation, responses, and usage statistics.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Enumeration for message roles in conversation context."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ContextType(str, Enum):
    """Enumeration for different types of conversation contexts."""
    CHATBOT = "chatbot"
    VOICE_AGENT = "voice_agent"
    TEACHING_ASSISTANT = "teaching_assistant"


class ContextMessage(BaseModel):
    """
    Single message in a conversation context.
    
    Represents an individual message with role identification,
    content, timestamp, and optional metadata for enhanced context.
    """
    
    message_id: UUID = Field(..., description="Unique identifier for the message")
    role: MessageRole = Field(..., description="Role of the message sender (user, assistant, or system)")
    content: str = Field(
        ..., 
        min_length=1, 
        max_length=2000,
        description="Message content text, limited to 2000 characters"
    )
    timestamp: datetime = Field(..., description="UTC timestamp when the message was created")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata dictionary for additional message context"
    )
    
    @validator('content')
    def validate_content_not_empty(cls, v):
        """Ensure content is not just whitespace."""
        if not v.strip():
            raise ValueError('Content cannot be empty or whitespace only')
        return v.strip()
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        schema_extra = {
            "example": {
                "message_id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "user",
                "content": "Hello, I need help with my course enrollment.",
                "timestamp": "2024-01-15T10:30:00Z",
                "metadata": {
                    "source": "web_chat",
                    "user_agent": "Mozilla/5.0",
                    "ip_address": "192.168.1.1"
                }
            }
        }


class ContextCreateRequest(BaseModel):
    """
    Request model for creating a new conversation context.
    
    Contains user identification, context type specification,
    and optional initial messages to start the conversation.
    """
    
    user_id: UUID = Field(..., description="UUID of the user creating the context")
    context_type: ContextType = Field(..., description="Type of conversation context being created")
    initial_messages: Optional[List[ContextMessage]] = Field(
        default=None,
        description="Optional list of initial messages to populate the context"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata for the conversation context"
    )
    
    @validator('initial_messages')
    def validate_initial_messages_limit(cls, v):
        """Limit initial messages to prevent abuse."""
        if v and len(v) > 10:
            raise ValueError('Cannot create context with more than 10 initial messages')
        return v
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "context_type": "chatbot",
                "initial_messages": [
                    {
                        "message_id": "123e4567-e89b-12d3-a456-426614174001",
                        "role": "user",
                        "content": "Hello, I want to learn about Python programming.",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "metadata": {"source": "web_interface"}
                    }
                ],
                "metadata": {
                    "session_id": "abc123",
                    "platform": "web",
                    "referrer": "course_catalog"
                }
            }
        }


class ContextResponse(BaseModel):
    """
    Response model containing complete conversation context information.
    
    Includes all context details, messages, counts, and timestamps
    for comprehensive context management.
    """
    
    context_id: UUID = Field(..., description="Unique identifier for the conversation context")
    user_id: UUID = Field(..., description="UUID of the user who owns this context")
    context_type: ContextType = Field(..., description="Type of conversation context")
    messages: List[ContextMessage] = Field(
        default_factory=list,
        description="List of all messages in the conversation context"
    )
    message_count: int = Field(
        default=0,
        ge=0,
        description="Total number of messages in the context"
    )
    created_at: datetime = Field(..., description="UTC timestamp when the context was created")
    updated_at: datetime = Field(..., description="UTC timestamp when the context was last updated")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata associated with the context"
    )
    
    @validator('message_count')
    def validate_message_count_matches(cls, v, values):
        """Ensure message_count matches the actual number of messages."""
        if 'messages' in values and len(values['messages']) != v:
            raise ValueError('message_count must match the number of messages')
        return v
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        schema_extra = {
            "example": {
                "context_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "context_type": "teaching_assistant",
                "messages": [
                    {
                        "message_id": "123e4567-e89b-12d3-a456-426614174002",
                        "role": "user",
                        "content": "Explain the concept of machine learning",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "metadata": {"topic": "ML_basics"}
                    },
                    {
                        "message_id": "123e4567-e89b-12d3-a456-426614174003",
                        "role": "assistant",
                        "content": "Machine learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed.",
                        "timestamp": "2024-01-15T10:30:15Z",
                        "metadata": {"confidence": 0.95, "sources": ["textbook_ch1"]}
                    }
                ],
                "message_count": 2,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:15Z",
                "metadata": {
                    "course_id": "CS101",
                    "lesson_topic": "introduction_to_ml"
                }
            }
        }


class AddMessageRequest(BaseModel):
    """
    Request model for adding a new message to an existing conversation context.
    
    Specifies the context to update, message role, content,
    and optional metadata for the new message.
    """
    
    context_id: UUID = Field(..., description="UUID of the context to add the message to")
    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Message content text, limited to 2000 characters"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata for the message"
    )
    
    @validator('content')
    def validate_content_not_empty(cls, v):
        """Ensure content is not just whitespace."""
        if not v.strip():
            raise ValueError('Content cannot be empty or whitespace only')
        return v.strip()
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "context_id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "user",
                "content": "Can you provide more examples of supervised learning algorithms?",
                "metadata": {
                    "follow_up_question": True,
                    "topic": "supervised_learning",
                    "urgency": "normal"
                }
            }
        }


class ContextStatsResponse(BaseModel):
    """
    Response model containing conversation context usage statistics.
    
    Provides comprehensive analytics about context usage,
    message distribution, and activity patterns over a specified period.
    """
    
    total_contexts: int = Field(
        ge=0,
        description="Total number of conversation contexts in the system"
    )
    total_messages: int = Field(
        ge=0,
        description="Total number of messages across all contexts"
    )
    message_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Breakdown of message counts by role (user, assistant, system)"
    )
    context_type_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Breakdown of contexts by type (chatbot, voice_agent, teaching_assistant)"
    )
    active_contexts: int = Field(
        ge=0,
        description="Number of contexts that have been active in the specified period"
    )
    avg_messages_per_context: float = Field(
        ge=0,
        description="Average number of messages per context"
    )
    period_start: datetime = Field(..., description="Start of the statistics period (UTC)")
    period_end: datetime = Field(..., description="End of the statistics period (UTC)")
    
    @validator('avg_messages_per_context')
    def calculate_avg_messages(cls, v, values):
        """Calculate average messages per context if not provided."""
        if 'total_contexts' in values and 'total_messages' in values:
            if values['total_contexts'] > 0:
                calculated_avg = values['total_messages'] / values['total_contexts']
                return round(calculated_avg, 2)
        return v
    
    @validator('period_end')
    def validate_period_end_after_start(cls, v, values):
        """Ensure period_end is after period_start."""
        if 'period_start' in values and v <= values['period_start']:
            raise ValueError('period_end must be after period_start')
        return v
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        schema_extra = {
            "example": {
                "total_contexts": 1250,
                "total_messages": 8750,
                "message_breakdown": {
                    "user": 4200,
                    "assistant": 4100,
                    "system": 450
                },
                "context_type_breakdown": {
                    "chatbot": 800,
                    "voice_agent": 300,
                    "teaching_assistant": 150
                },
                "active_contexts": 890,
                "avg_messages_per_context": 7.0,
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-31T23:59:59Z"
            }
        }
