"""
Chatbot Module Schemas

This module contains Pydantic models for chatbot functionality including:
- Chat messages and sessions
- Message sending and responses
- Lead capture
- Chatbot performance statistics

File: /app/schemas/chatbot.py
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Enumeration for chat message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSessionStatus(str, Enum):
    """Enumeration for chat session status."""
    ACTIVE = "active"
    CLOSED = "closed"
    PAUSED = "paused"
    TRANSFERRED = "transferred"


class ChatMessage(BaseModel):
    """
    Single message in a chat conversation.
    
    Represents one message exchanged between user and AI assistant
    with metadata including role, content, timestamp, and confidence score.
    """
    
    message_id: UUID = Field(
        ..., 
        description="Unique identifier for the message"
    )
    role: MessageRole = Field(
        ..., 
        description="Role of the message sender (user, assistant, system)"
    )
    content: str = Field(
        ..., 
        min_length=1, 
        max_length=2000, 
        description="Message content text"
    )
    timestamp: datetime = Field(
        ..., 
        description="When the message was created"
    )
    confidence: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="AI confidence score for the response (0-1)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional message metadata"
    )
    
    @validator('content')
    def validate_content_not_empty(cls, v):
        """Ensure content is not just whitespace."""
        if not v.strip():
            raise ValueError('Message content cannot be empty or whitespace only')
        return v.strip()


class ChatSessionCreateRequest(BaseModel):
    """
    Request schema for creating a new chat session.
    
    Contains information needed to initialize a new chatbot conversation
    including visitor identification and initial context.
    """
    
    lead_id: Optional[UUID] = Field(
        None, 
        description="Associated lead ID if visitor is a known lead"
    )
    visitor_id: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Unique identifier for the website visitor"
    )
    page_url: str = Field(
        ..., 
        max_length=500, 
        description="URL of the page where chat was initiated"
    )
    initial_message: Optional[str] = Field(
        None, 
        max_length=2000, 
        description="First message from the user to start the conversation"
    )
    visitor_info: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional visitor information (location, device, etc.)"
    )
    
    @validator('page_url')
    def validate_page_url(cls, v):
        """Basic URL validation."""
        if not (v.startswith('http://') or v.startswith('https://') or v.startswith('/')):
            raise ValueError('Page URL must be a valid URL or path')
        return v


class ChatSessionResponse(BaseModel):
    """
    Complete chat session details with messages and metadata.
    
    Contains all information about a chat session including message history,
    current status, and session metrics.
    """
    
    session_id: UUID = Field(
        ..., 
        description="Unique identifier for the chat session"
    )
    lead_id: Optional[UUID] = Field(
        None, 
        description="Associated lead ID if applicable"
    )
    visitor_id: str = Field(
        ..., 
        description="Visitor identifier"
    )
    page_url: str = Field(
        ..., 
        description="Page where chat was initiated"
    )
    status: ChatSessionStatus = Field(
        ..., 
        description="Current session status"
    )
    messages: List[ChatMessage] = Field(
        default_factory=list, 
        description="List of all messages in the session"
    )
    created_at: datetime = Field(
        ..., 
        description="When the session was created"
    )
    updated_at: datetime = Field(
        ..., 
        description="When the session was last updated"
    )
    duration_minutes: Optional[float] = Field(
        None, 
        ge=0.0, 
        description="Session duration in minutes"
    )
    satisfaction_rating: Optional[int] = Field(
        None, 
        ge=1, 
        le=5, 
        description="User satisfaction rating (1-5 stars)"
    )
    tags: Optional[List[str]] = Field(
        default_factory=list, 
        description="Tags categorizing the conversation"
    )


class SendMessageRequest(BaseModel):
    """
    Request schema for sending a message in a chat session.
    
    Used to send user messages to the AI assistant within
    an existing chat session.
    """
    
    session_id: UUID = Field(
        ..., 
        description="ID of the chat session"
    )
    content: str = Field(
        ..., 
        min_length=1, 
        max_length=2000, 
        description="Message content to send"
    )
    message_type: Optional[str] = Field(
        "text", 
        description="Type of message (text, image, file, etc.)"
    )
    
    @validator('content')
    def validate_content_not_empty(cls, v):
        """Ensure content is not just whitespace."""
        if not v.strip():
            raise ValueError('Message content cannot be empty or whitespace only')
        return v.strip()


class SendMessageResponse(BaseModel):
    """
    AI response to user message with metadata.
    
    Contains the AI assistant's response message along with
    processing metadata and confidence scores.
    """
    
    message: ChatMessage = Field(
        ..., 
        description="The AI assistant's response message"
    )
    session_id: UUID = Field(
        ..., 
        description="ID of the chat session"
    )
    processing_time_ms: Optional[float] = Field(
        None, 
        ge=0.0, 
        description="Time taken to process the message in milliseconds"
    )
    suggested_actions: Optional[List[str]] = Field(
        default_factory=list, 
        description="Suggested follow-up actions for the user"
    )
    intent_detected: Optional[str] = Field(
        None, 
        description="Detected user intent from the message"
    )
    entities_extracted: Optional[Dict[str, Any]] = Field(
        None, 
        description="Extracted entities from user message"
    )


class CaptureLeadRequest(BaseModel):
    """
    Request schema for capturing lead information from chat.
    
    Used when a chat visitor provides contact information
    and converts to a lead during the conversation.
    """
    
    session_id: UUID = Field(
        ..., 
        description="ID of the chat session where lead was captured"
    )
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Lead's full name"
    )
    email: str = Field(
        ..., 
        max_length=254, 
        description="Lead's email address"
    )
    phone: Optional[str] = Field(
        None, 
        max_length=20, 
        description="Lead's phone number"
    )
    course_interest: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Course the lead is interested in"
    )
    message: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Additional message or requirements from lead"
    )
    lead_source: str = Field(
        default="chatbot", 
        description="Source of the lead capture"
    )
    qualification_score: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=100.0, 
        description="AI-calculated lead qualification score (0-100)"
    )
    
    @validator('email')
    def validate_email(cls, v):
        """Basic email validation."""
        if '@' not in v or '.' not in v.split('@')[1]:
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('name')
    def validate_name_not_empty(cls, v):
        """Ensure name is not just whitespace."""
        if not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip()


class ChatbotStatsResponse(BaseModel):
    """
    Chatbot performance statistics and metrics.
    
    Comprehensive statistics about chatbot performance including
    conversation metrics, user satisfaction, and operational data.
    """
    
    total_sessions: int = Field(
        ..., 
        ge=0, 
        description="Total number of chat sessions"
    )
    active_sessions: int = Field(
        ..., 
        ge=0, 
        description="Currently active chat sessions"
    )
    total_messages: int = Field(
        ..., 
        ge=0, 
        description="Total messages processed"
    )
    leads_captured: int = Field(
        ..., 
        ge=0, 
        description="Number of leads captured through chat"
    )
    avg_session_duration: float = Field(
        ..., 
        ge=0.0, 
        description="Average session duration in minutes"
    )
    avg_messages_per_session: float = Field(
        ..., 
        ge=0.0, 
        description="Average number of messages per session"
    )
    lead_conversion_rate: float = Field(
        ..., 
        ge=0.0, 
        le=100.0, 
        description="Percentage of sessions that converted to leads"
    )
    avg_response_time_ms: float = Field(
        ..., 
        ge=0.0, 
        description="Average AI response time in milliseconds"
    )
    user_satisfaction_avg: Optional[float] = Field(
        None, 
        ge=1.0, 
        le=5.0, 
        description="Average user satisfaction rating (1-5 stars)"
    )
    top_intents: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Most common user intents detected"
    )
    busiest_hours: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Peak chat activity hours"
    )
    period_start: datetime = Field(
        ..., 
        description="Start of the reporting period"
    )
    period_end: datetime = Field(
        ..., 
        description="End of the reporting period"
    )
    
    class Config:
        """Pydantic configuration with example schema."""
        json_schema_extra = {
            "example": {
                "total_sessions": 1250,
                "active_sessions": 23,
                "total_messages": 15680,
                "leads_captured": 187,
                "avg_session_duration": 8.5,
                "avg_messages_per_session": 12.5,
                "lead_conversion_rate": 14.96,
                "avg_response_time_ms": 850.0,
                "user_satisfaction_avg": 4.2,
                "top_intents": [
                    {"intent": "course_inquiry", "count": 456, "percentage": 36.5},
                    {"intent": "pricing_question", "count": 312, "percentage": 25.0},
                    {"intent": "schedule_demo", "count": 189, "percentage": 15.1}
                ],
                "busiest_hours": [
                    {"hour": 14, "session_count": 89},
                    {"hour": 15, "session_count": 76},
                    {"hour": 10, "session_count": 71}
                ],
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-31T23:59:59Z"
            }
        }
