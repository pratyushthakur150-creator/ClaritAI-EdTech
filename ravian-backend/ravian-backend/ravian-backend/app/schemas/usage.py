from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel
from typing_extensions import Literal


class UsageMetrics(BaseModel):
    """Current or historical usage metrics for a tenant."""

    tenant_id: UUID
    period: str  # e.g. "2024-02"

    leads_created: int
    leads_limit: int

    calls_made: int
    calls_limit: int

    active_students: int
    students_limit: int

    credits_consumed: float
    credits_limit: int

    plan: str  # Display name: "Starter", "Growth", "Enterprise"


class UsageHistoryResponse(BaseModel):
    """History of usage metrics over multiple periods."""

    history: List[UsageMetrics]
    total_months: int


class UsageCheckRequest(BaseModel):
    """Request payload for checking usage limits for a specific resource."""

    resource_type: Literal["leads", "calls", "students"]


class UsageCheckResponse(BaseModel):
    """Response describing whether a tenant is within plan limits."""

    allowed: bool
    current_usage: int
    limit: int
    remaining: int
    message: str
    upgrade_required: bool


class PlanLimits(BaseModel):
    """Plan configuration and limits."""

    plan: Literal["Starter", "Growth", "Enterprise"]
    leads_limit: int
    calls_limit: int
    students_limit: int
    credits_limit: int
    price_per_month: float

