"""
Schemas package - exports all Pydantic schemas
"""

# Analytics schemas
from .analytics import (
    DashboardOverviewResponse,
    FunnelAnalysisResponse,
    TeamPerformanceResponse,
    RevenueAnalyticsResponse,
    CustomReportRequest,
    CustomReportResponse,
)

# Auth schemas
from .auth import (
    TokenResponse,
    TokenRequest,
    LoginRequest,
    RegisterRequest,
    UserContext,
    TenantContext,
    UserProfile,
)

# Lead schemas (matching what's actually in lead.py)
from .lead import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadTimeline,
    LeadAssign,
)

# Call schemas
from .call import (
    CallLogCreate,
    CallLogUpdate,
    CallLogResponse,
    CallLogListResponse,
    TriggerCallRequest,
    TriggerCallResponse,
)

# Demo schemas
from .demo import (
    DemoCreate,
    DemoUpdate,
    DemoResponse,
    DemoListResponse,
    DemoOutcomeRequest,
)

# Enrollment schemas
from .enrollment import (
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentResponse,
)

__all__ = [
    # Analytics
    "DashboardOverviewResponse",
    "FunnelAnalysisResponse",
    "TeamPerformanceResponse",
    "RevenueAnalyticsResponse",
    "CustomReportRequest",
    "CustomReportResponse",
    
    # Auth
    "TokenResponse",
    "TokenRequest",
    "LoginRequest",
    "RegisterRequest",
    "UserContext",
    "TenantContext",
    "UserProfile",
    
    # Lead
    "LeadCreate",
    "LeadUpdate",
    "LeadResponse",
    "LeadTimeline",
    "LeadAssign",
    
    # Call
    "CallLogCreate",
    "CallLogUpdate",
    "CallLogResponse",
    "CallLogListResponse",
    "TriggerCallRequest",
    "TriggerCallResponse",
    
    # Demo
    "DemoCreate",
    "DemoUpdate",
    "DemoResponse",
    "DemoListResponse",
    "DemoOutcomeRequest",
    
    # Enrollment
    "EnrollmentCreate",
    "EnrollmentUpdate",
    "EnrollmentResponse",
]