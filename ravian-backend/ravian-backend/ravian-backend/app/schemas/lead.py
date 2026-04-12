"""
Pydantic schemas for the Leads API.
This module defines all request/response schemas for lead management operations.
"""

from typing import Dict, List, Literal, Optional, Any
from uuid import UUID
from datetime import datetime
import re

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from pydantic import constr

# Phone number validation using field_validator instead of custom type
PHONE_REGEX = re.compile(r'^\+?1?-?\.?\s?\(?([0-9]{3})\)?[-\.\s]?([0-9]{3})[-\.\s]?([0-9]{4})$|^\+?([1-9]\d{0,3})?[-.\s]?\(?([0-9]{1,4})\)?[-.\s]?([0-9]{1,4})[-.\s]?([0-9]{1,9})$')

class LeadCreate(BaseModel):
    """Schema for creating a new lead"""
    
    name: str = Field(
        ..., 
        min_length=1,
        max_length=200,
        description="Full name of the lead",
        examples=["John Smith"]
    )
    
    phone: str = Field(
        ..., 
        description="Phone number in any standard format",
        examples=["+1-555-123-4567"]
    )
    
    email: Optional[EmailStr] = Field(
        None, 
        description="Email address (optional)",
        examples=["john.smith@email.com"]
    )
    
    source: Literal["WEBSITE", "CHATBOT", "REFERRAL", "SOCIAL_MEDIA", "ADVERTISING", "EMAIL_CAMPAIGN", "DIRECT", "OTHER"] = Field(
        ...,
        description="Source of the lead acquisition (must match database enum)",
        examples=["CHATBOT"]
    )
    
    intent: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Detected or stated intent/interest",
        examples=["Interested in data science bootcamp for career transition"]
    )
    
    interested_courses: List[str] = Field(
        ..., 
        description="List of courses the lead is interested in",
        examples=[["Data Science Bootcamp", "Machine Learning Fundamentals"]]
    )
    
    urgency: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        ...,
        description="Urgency level of the lead (must match database enum)",
        examples=["HIGH"]
    )
    
    chatbot_context: Optional[Dict[str, Any]] = Field(
        None, 
        description="Full conversation JSON from chatbot interaction"
    )
    
    utm_params: Optional[Dict[str, str]] = Field(
        None, 
        description="UTM tracking parameters"
    )

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format"""
        if not isinstance(v, str):
            raise TypeError('Phone must be a string')
        
        # Remove common formatting characters for validation
        cleaned = re.sub(r'[\s\-\.\(\)]', '', v)
        
        # Basic validation - must be 10-15 digits possibly with + prefix
        if not re.match(r'^\+?\d{10,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        
        return v

    @field_validator('interested_courses')
    @classmethod
    def validate_courses(cls, v):
        if not v:
            raise ValueError('At least one interested course is required')
        return [course.strip() for course in v if course.strip()]

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Jane Doe",
                "phone": "+1-555-987-6543",
                "email": "jane.doe@email.com",
                "source": "CHATBOT",
                "intent": "Career change to data science, has programming background",
                "interested_courses": ["Data Science Bootcamp", "Python for Data Analysis"],
                "urgency": "HIGH",
                "chatbot_context": {
                    "conversation_id": "conv_456",
                    "engagement_score": 0.9,
                    "session_duration": 420
                },
                "utm_params": {
                    "utm_source": "facebook",
                    "utm_medium": "social",
                    "utm_campaign": "career_change_2024"
                }
            }
        }
    }


class LeadUpdate(BaseModel):
    """Schema for updating an existing lead"""
    
    status: Optional[Literal["NEW", "CONTACTED", "QUALIFIED", "DEMO_SCHEDULED", "DEMO_COMPLETED", "ENROLLED", "LOST", "NURTURING"]] = Field(
        None,
        description="Current status of the lead (must match database enum)",
        examples=["CONTACTED"]
    )
    
    intent: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Updated intent/interest information",
        examples=["Specifically interested in evening data science classes"]
    )
    
    urgency: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = Field(
        None,
        description="Updated urgency level (must match database enum)",
        examples=["MEDIUM"]
    )
    
    assigned_to: Optional[UUID] = Field(
        None, 
        description="UUID of the team member assigned to this lead"
    )
    
    notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Additional notes about the lead"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "QUALIFIED",
                "urgency": "HIGH",
                "assigned_to": "123e4567-e89b-12d3-a456-426614174000",
                "notes": "Strong technical background, ready to start immediately"
            }
        }
    }


class AssignedUser(BaseModel):
    """Nested schema for assigned user information"""
    id: UUID
    name: str = "Unknown"
    email: str

    model_config = {
        "from_attributes": True,
    }

    @model_validator(mode="wrap")
    @classmethod
    def build_from_user(cls, values, handler):
        # If it's an ORM object (User model), extract fields manually
        if hasattr(values, 'first_name'):
            first = getattr(values, 'first_name', '') or ''
            last = getattr(values, 'last_name', '') or ''
            full_name = f"{first} {last}".strip() or "Unknown"
            return cls(
                id=values.id,
                name=full_name,
                email=values.email,
            )
        # Otherwise use default validation (dict input)
        return handler(values)


def _enum_to_str(v: Any) -> Any:
    """Convert SQLAlchemy/Python enum to string for JSON serialization."""
    if v is None:
        return v
    if hasattr(v, "value"):
        return v.value
    return v


class LeadResponse(BaseModel):
    """Schema for lead response data"""

    id: UUID = Field(..., description="Unique identifier for the lead")
    name: str = Field(..., description="Full name of the lead")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    source: str = Field(..., description="Source of lead acquisition")
    status: str = Field(..., description="Current status of the lead")
    intent: Optional[str] = Field("", description="Lead's stated intent or interest")
    interested_courses: List[str] = Field(default_factory=list, description="List of courses the lead is interested in")

    @field_validator("interested_courses", mode="before")
    @classmethod
    def coerce_interested_courses(cls, v):
        if v is None:
            return []
        return v
    urgency: str = Field("MEDIUM", description="Urgency level")
    created_at: datetime = Field(..., description="Timestamp when lead was created")
    updated_at: datetime = Field(..., description="Timestamp when lead was last updated")
    assigned_user: Optional[AssignedUser] = Field(None, serialization_alias="assigned_to", description="Information about assigned team member")
    chatbot_engagement_score: Optional[float] = Field(None, description="Engagement score from chatbot interaction (0.0-1.0)")
    last_contact_at: Optional[datetime] = Field(None, description="Timestamp of last contact attempt")
    next_action: Optional[str] = Field(None, description="Recommended next action")

    @field_validator("source", "status", "urgency", mode="before")
    @classmethod
    def convert_enum_to_str(cls, v: Any) -> Any:
        return _enum_to_str(v)

    model_config = {
        "from_attributes": True,
    }


class TimelineEvent(BaseModel):
    """Schema for individual timeline events"""
    type: str = Field(..., description="Type of event")
    timestamp: datetime = Field(..., description="When the event occurred")
    data: Dict[str, Any] = Field(..., description="Event-specific data")


class LeadTimeline(BaseModel):
    """Schema for lead timeline containing all events"""
    events: List[TimelineEvent] = Field(..., description="Chronological list of events for this lead")


class LeadAssign(BaseModel):
    """Schema for assigning a lead to a team member"""
    lead_id: UUID = Field(..., description="UUID of the lead to assign")
    assigned_to: UUID = Field(..., description="UUID of team member to assign to")
    reason: Optional[str] = Field(None, description="Reason for assignment")
    priority: Optional[Literal["low", "medium", "high"]] = Field("medium", description="Priority level for this assignment")