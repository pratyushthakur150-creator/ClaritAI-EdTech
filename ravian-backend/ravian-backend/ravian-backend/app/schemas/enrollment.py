"""
Enrollment schemas for AI EdTech CRM platform.
Handles student enrollment, payment tracking, and course registration.
"""

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class EnrollmentCreate(BaseModel):
    """Schema for creating new enrollment records."""
    
    lead_id: UUID = Field(..., description="Unique identifier of the lead being enrolled")
    course_id: UUID = Field(..., description="Unique identifier of the course")
    batch_id: str = Field(..., description="Unique identifier of the batch")
    total_amount: float = Field(..., gt=0, description="Total course amount (must be positive)")
    payment_status: Literal["PENDING", "PARTIAL", "PAID"] = Field(
        default="PENDING", 
        description="Current payment status"
    )
    amount_paid: float = Field(
        default=0.0, 
        ge=0, 
        description="Amount already paid (must be non-negative)"
    )
    
    @field_validator('amount_paid')
    @classmethod
    def validate_amount_paid(cls, v, info):
        """Validate that amount_paid doesn't exceed total_amount."""
        if 'total_amount' in info.data and v > info.data['total_amount']:
            raise ValueError('Amount paid cannot exceed total amount')
        return v
    
    @field_validator('payment_status')
    @classmethod
    def validate_payment_status_consistency(cls, v, info):
        """Validate payment status consistency with amount_paid."""
        if 'amount_paid' in info.data and 'total_amount' in info.data:
            amount_paid = info.data['amount_paid']
            total_amount = info.data['total_amount']
            
            if v == "PAID" and amount_paid < total_amount:
                raise ValueError('Payment status cannot be paid if amount paid is less than total')
            elif v == "PENDING" and amount_paid > 0:
                raise ValueError('Payment status cannot be pending if amount has been paid')
        
        return v

    model_config = {
        "json_encoders": {
            UUID: str,
            datetime: lambda dt: dt.isoformat()
        },
        "from_attributes": True,
        "validate_assignment": True
    }


class EnrollmentUpdate(BaseModel):
    """Schema for updating enrollment records."""
    
    payment_status: Optional[Literal["PENDING", "PARTIAL", "PAID"]] = Field(
        None, 
        description="Updated payment status"
    )
    amount_paid: Optional[float] = Field(
        None, 
        ge=0, 
        description="Updated amount paid (must be non-negative)"
    )
    notes: Optional[str] = Field(
        None, 
        max_length=1000, 
        description="Additional notes about the enrollment"
    )
    
    @field_validator('amount_paid')
    @classmethod
    def validate_amount_paid(cls, v):
        """Ensure amount_paid is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError('Amount paid must be non-negative')
        return v

    model_config = {
        "json_encoders": {
            UUID: str,
            datetime: lambda dt: dt.isoformat()
        },
        "from_attributes": True,
        "validate_assignment": True,
        "exclude_none": True  # Exclude None values in serialization
    }


def _enum_to_str(v: Any) -> Any:
    """Convert SQLAlchemy/Python enum to string for JSON serialization."""
    if v is None:
        return v
    if hasattr(v, "value"):
        return v.value
    return v


class EnrollmentResponse(BaseModel):
    """Schema for enrollment response data."""

    id: UUID = Field(..., description="Unique enrollment identifier")
    lead: dict = Field(..., description="Lead information: {id, name, phone}")
    course: dict = Field(..., description="Course information: {id, name}")
    batch_id: Optional[str] = Field(None, description="Batch identifier (optional)")
    enrolled_at: datetime = Field(..., description="Enrollment timestamp")
    payment_status: str = Field(..., description="Current payment status")
    total_amount: float = Field(..., description="Total course amount")
    amount_paid: float = Field(..., description="Amount already paid")
    student_id: Optional[UUID] = Field(None, description="Student ID created after enrollment")
    created_at: datetime = Field(..., description="Record creation timestamp")

    @field_validator("payment_status", mode="before")
    @classmethod
    def convert_enum_to_str(cls, v: Any) -> Any:
        return _enum_to_str(v)

    @field_validator('lead')
    @classmethod
    def validate_lead_dict(cls, v):
        """Validate lead dictionary structure."""
        required_keys = {'id', 'name', 'phone'}
        if not isinstance(v, dict):
            raise ValueError('Lead must be a dictionary')
        
        missing_keys = required_keys - set(v.keys())
        if missing_keys:
            raise ValueError(f'Lead dictionary missing required keys: {missing_keys}')
        
        return v
    
    @field_validator('course')
    @classmethod
    def validate_course_dict(cls, v):
        """Validate course dictionary structure."""
        required_keys = {'id', 'name'}
        if not isinstance(v, dict):
            raise ValueError('Course must be a dictionary')
        
        missing_keys = required_keys - set(v.keys())
        if missing_keys:
            raise ValueError(f'Course dictionary missing required keys: {missing_keys}')
        
        return v
    
    @field_validator('payment_status')
    @classmethod
    def validate_payment_status(cls, v):
        """Validate payment status values."""
        valid_statuses = {"PENDING", "PARTIAL", "COMPLETED", "PAID", "FAILED", "REFUNDED", "CANCELLED"}
        if v not in valid_statuses:
            raise ValueError(f'Payment status must be one of: {valid_statuses}')
        return v

    model_config = {
        "json_encoders": {
            UUID: str,
            datetime: lambda dt: dt.isoformat()
        },
        "from_attributes": True,
        "validate_assignment": True,
        "use_enum_values": True,
        "arbitrary_types_allowed": False
    }


# Additional utility schemas for enrollment operations
class EnrollmentFilter(BaseModel):
    """Schema for filtering enrollment records."""
    
    course_id: Optional[UUID] = None
    batch_id: Optional[UUID] = None
    payment_status: Optional[Literal["PENDING", "PARTIAL", "PAID"]] = None
    enrolled_after: Optional[datetime] = None
    enrolled_before: Optional[datetime] = None
    
    model_config = {
        "json_encoders": {
            UUID: str,
            datetime: lambda dt: dt.isoformat()
        },
        "from_attributes": True
    }


class EnrollmentSummary(BaseModel):
    """Schema for enrollment summary statistics."""
    
    total_enrollments: int = Field(..., ge=0, description="Total number of enrollments")
    pending_payments: int = Field(..., ge=0, description="Enrollments with pending payments")
    partial_payments: int = Field(..., ge=0, description="Enrollments with partial payments")
    completed_payments: int = Field(..., ge=0, description="Enrollments with completed payments")
    total_revenue: float = Field(..., ge=0, description="Total revenue from enrollments")
    pending_amount: float = Field(..., ge=0, description="Total pending payment amount")
    
    model_config = {
        "from_attributes": True,
        "validate_assignment": True
    }