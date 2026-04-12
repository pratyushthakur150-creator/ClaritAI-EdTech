"""
Usage Schemas
File: /app/schemas/usage.py
"""

from pydantic import BaseModel, Field
from typing import List
from uuid import UUID
from typing_extensions import Literal
import json


class UsageMetrics(BaseModel):
    """Usage metrics for a tenant in a specific period"""
    tenant_id: UUID
    period: str = Field(..., description="Period in format YYYY-MM")
    leads_created: int = Field(..., ge=0, description="Number of leads created")
    leads_limit: int = Field(..., gt=0, description="Maximum leads allowed")
    calls_made: int = Field(..., ge=0, description="Number of calls made")
    calls_limit: int = Field(..., gt=0, description="Maximum calls allowed")
    active_students: int = Field(..., ge=0, description="Number of active students")
    students_limit: int = Field(..., gt=0, description="Maximum students allowed")
    credits_consumed: float = Field(..., ge=0, description="Credits consumed")
    credits_limit: float = Field(..., gt=0, description="Maximum credits allowed")
    plan: Literal["Starter", "Growth", "Enterprise"] = Field(..., description="Current plan")

    @property
    def leads_remaining(self) -> int:
        """Calculate remaining leads"""
        return max(0, self.leads_limit - self.leads_created)

    @property
    def calls_remaining(self) -> int:
        """Calculate remaining calls"""
        return max(0, self.calls_limit - self.calls_made)

    @property
    def students_remaining(self) -> int:
        """Calculate remaining students"""
        return max(0, self.students_limit - self.active_students)

    class Config:
        json_encoders = {
            UUID: str
        }


class PlanLimits(BaseModel):
    """Plan limits and pricing information"""
    plan: Literal["Starter", "Growth", "Enterprise"] = Field(..., description="Plan type")
    leads_limit: int = Field(..., gt=0, description="Maximum leads allowed")
    calls_limit: int = Field(..., gt=0, description="Maximum calls allowed")
    students_limit: int = Field(..., gt=0, description="Maximum students allowed")
    credits_limit: float = Field(..., gt=0, description="Maximum credits allowed")
    price_per_month: float = Field(..., ge=0, description="Monthly price")


class UsageCheckRequest(BaseModel):
    """Request to check usage for a specific resource type"""
    resource_type: Literal["leads", "calls", "students"] = Field(
        ..., description="Type of resource to check"
    )


class UsageCheckResponse(BaseModel):
    """Response for usage check containing current status"""
    allowed: bool = Field(..., description="Whether action is allowed")
    current_usage: int = Field(..., ge=0, description="Current usage count")
    limit: int = Field(..., gt=0, description="Usage limit")
    remaining: int = Field(..., ge=0, description="Remaining usage")
    message: str = Field(..., description="Status message")
    upgrade_required: bool = Field(default=False, description="Whether upgrade is required")


class UsageHistoryResponse(BaseModel):
    """Response containing usage history for multiple periods"""
    history: List[UsageMetrics] = Field(..., description="List of usage metrics by period")
    total_months: int = Field(..., ge=0, description="Total number of months in history")


__all__ = [
    "UsageMetrics",
    "PlanLimits", 
    "UsageCheckRequest",
    "UsageCheckResponse",
    "UsageHistoryResponse"
]