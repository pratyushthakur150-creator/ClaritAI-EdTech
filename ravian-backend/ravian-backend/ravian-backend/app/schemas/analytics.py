"""
Analytics Module Pydantic Schemas

This module contains all Pydantic model schemas for the Analytics module,
including dashboard metrics, conversion funnels, time series data, team performance,
revenue analytics, and custom reports.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class DashboardMetrics(BaseModel):
    """
    Core dashboard metrics for overview display.
    
    Contains all key performance indicators and metrics
    used in the main dashboard overview.
    """
    total_leads: int = Field(..., ge=0, description="Total number of leads in the period")
    active_leads: int = Field(..., ge=0, description="Number of currently active leads")
    converted_leads: int = Field(..., ge=0, description="Number of converted leads")
    total_calls: int = Field(..., ge=0, description="Total number of calls made")
    total_demos: int = Field(..., ge=0, description="Total number of demos conducted")
    total_enrollments: int = Field(..., ge=0, description="Total number of enrollments")
    revenue: float = Field(..., ge=0, description="Total revenue generated")
    conversion_rate: float = Field(..., ge=0, le=100, description="Overall conversion rate as percentage")
    demo_attendance_rate: float = Field(..., ge=0, le=100, description="Demo attendance rate as percentage")
    call_answer_rate: float = Field(..., ge=0, le=100, description="Call answer rate as percentage")
    period_start: datetime = Field(..., description="Start date of the reporting period")
    period_end: datetime = Field(..., description="End date of the reporting period")


class DashboardOverviewResponse(BaseModel):
    """
    Complete dashboard overview response containing metrics and additional data.
    
    Provides comprehensive dashboard data including metrics, trends,
    top courses, and recent activities.
    """
    metrics: DashboardMetrics = Field(..., description="Core dashboard metrics")
    trends: Dict[str, float] = Field(..., description="Trend data for key metrics")
    top_courses: List[Dict[str, Any]] = Field(..., description="List of top performing courses")
    recent_activities: List[Dict[str, Any]] = Field(..., description="List of recent system activities")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metrics": {
                    "total_leads": 1250,
                    "active_leads": 340,
                    "converted_leads": 185,
                    "total_calls": 2100,
                    "total_demos": 420,
                    "total_enrollments": 185,
                    "revenue": 92500.00,
                    "conversion_rate": 14.8,
                    "demo_attendance_rate": 78.5,
                    "call_answer_rate": 65.2,
                    "period_start": "2024-01-01T00:00:00Z",
                    "period_end": "2024-01-31T23:59:59Z"
                },
                "trends": {
                    "leads": 12.5,
                    "calls": 8.3,
                    "demos": 15.7,
                    "enrollments": 9.2,
                    "revenue": 18.4
                },
                "top_courses": [
                    {
                        "course_id": "course_123",
                        "course_name": "Advanced Python Programming",
                        "enrollments": 45,
                        "revenue": 22500.00
                    },
                    {
                        "course_id": "course_456",
                        "course_name": "Data Science Fundamentals",
                        "enrollments": 38,
                        "revenue": 19000.00
                    }
                ],
                "recent_activities": [
                    {
                        "activity_id": "act_789",
                        "type": "enrollment",
                        "description": "New enrollment in Advanced Python Programming",
                        "timestamp": "2024-01-31T14:30:00Z",
                        "agent_name": "John Doe"
                    },
                    {
                        "activity_id": "act_790",
                        "type": "demo",
                        "description": "Demo scheduled for Data Science course",
                        "timestamp": "2024-01-31T13:15:00Z",
                        "agent_name": "Jane Smith"
                    }
                ]
            }
        }


class FunnelStage(BaseModel):
    """
    Individual stage in the conversion funnel.
    
    Represents a single step in the lead conversion process
    with associated metrics and rates.
    """
    stage: str = Field(..., description="Name of the funnel stage")
    count: int = Field(..., ge=0, description="Number of leads at this stage")
    conversion_rate: float = Field(..., ge=0, le=100, description="Conversion rate to next stage as percentage")
    drop_off_rate: float = Field(..., ge=0, le=100, description="Drop-off rate from this stage as percentage")


class ConversionFunnelResponse(BaseModel):
    """
    Complete conversion funnel analysis response.
    
    Contains all stages of the conversion funnel with
    overall metrics and bottleneck identification.
    """
    stages: List[FunnelStage] = Field(..., description="List of all funnel stages")
    overall_conversion_rate: float = Field(..., ge=0, le=100, description="End-to-end conversion rate")
    bottleneck_stage: str = Field(..., description="Stage with the highest drop-off rate")
    total_leads: int = Field(..., ge=0, description="Total leads entering the funnel")
    total_enrollments: int = Field(..., ge=0, description="Total enrollments from the funnel")
    date_range: Dict[str, datetime] = Field(..., description="Date range for the funnel analysis")


class FunnelAnalysisResponse(ConversionFunnelResponse):
    """
    Backwards-compatible alias for conversion funnel analysis response.
    
    Kept for compatibility with older imports referencing FunnelAnalysisResponse.
    """


class TimeSeriesDataPoint(BaseModel):
    """
    Single data point in a time series.
    
    Represents one point in time with associated
    metric value for trend analysis.
    """
    date: datetime = Field(..., description="Date and time of the data point")
    value: float = Field(..., description="Metric value at this point in time")
    metric: str = Field(..., description="Name of the metric being tracked")


class TimeSeriesResponse(BaseModel):
    """
    Time series data response for trend analysis.
    
    Contains series of data points over time with
    trend analysis and growth rate calculations.
    """
    metric: str = Field(..., description="Name of the metric being analyzed")
    data_points: List[TimeSeriesDataPoint] = Field(..., description="List of time-ordered data points")
    trend: str = Field(..., description="Overall trend direction (up, down, stable)")
    growth_rate: float = Field(..., description="Period-over-period growth rate as percentage")


class AgentPerformance(BaseModel):
    """
    Individual agent performance metrics.
    
    Contains comprehensive performance data for
    a single sales agent including optional satisfaction score.
    """
    agent_id: UUID = Field(..., description="Unique identifier for the agent")
    agent_name: str = Field(..., description="Full name of the agent")
    calls_made: int = Field(..., ge=0, description="Total number of calls made by the agent")
    demos_conducted: int = Field(..., ge=0, description="Total number of demos conducted")
    enrollments_generated: int = Field(..., ge=0, description="Total enrollments generated by the agent")
    conversion_rate: float = Field(..., ge=0, le=100, description="Agent's conversion rate as percentage")
    avg_call_duration: float = Field(..., ge=0, description="Average call duration in minutes")
    satisfaction_score: Optional[float] = Field(None, ge=0, le=10, description="Customer satisfaction score (0-10)")


class TeamPerformanceResponse(BaseModel):
    """
    Team-wide performance analytics response.
    
    Contains performance data for all agents with
    team averages and top performer identification.
    """
    agents: List[AgentPerformance] = Field(..., description="List of all agent performance data")
    team_avg_conversion: float = Field(..., ge=0, le=100, description="Team average conversion rate")
    top_performer: UUID = Field(..., description="Agent ID of the top performing agent")
    total_team_enrollments: int = Field(..., ge=0, description="Total enrollments generated by the team")


class RevenueBreakdown(BaseModel):
    """
    Revenue breakdown by course or category.
    
    Detailed revenue analysis for individual courses
    including enrollment counts and revenue shares.
    """
    course_id: Optional[str] = Field(None, description="Unique course identifier")
    course_name: str = Field(..., description="Name of the course")
    total_revenue: float = Field(..., ge=0, description="Total revenue generated from this course")
    enrollment_count: int = Field(..., ge=0, description="Number of enrollments for this course")
    avg_revenue_per_student: float = Field(..., ge=0, description="Average revenue per enrolled student")
    revenue_share_percent: float = Field(..., ge=0, le=100, description="Percentage share of total revenue")


class RevenueAnalyticsResponse(BaseModel):
    """
    Comprehensive revenue analytics response.
    
    Contains detailed revenue analysis including breakdowns,
    forecasts, and growth metrics.
    """
    total_revenue: float = Field(..., ge=0, description="Total revenue for the period")
    revenue_by_course: List[RevenueBreakdown] = Field(..., description="Revenue breakdown by course")
    monthly_revenue: List[TimeSeriesDataPoint] = Field(..., description="Monthly revenue time series")
    forecast_next_month: float = Field(..., ge=0, description="Forecasted revenue for next month")
    growth_rate: float = Field(..., description="Revenue growth rate as percentage")
    date_range: Dict[str, datetime] = Field(..., description="Date range for the revenue analysis")


class ReportRequest(BaseModel):
    """
    Custom report generation request.
    
    Parameters for generating custom analytics reports
    with flexible filtering and grouping options.
    """
    report_type: str = Field(..., description="Type of report to generate")
    date_from: datetime = Field(..., description="Start date for the report period")
    date_to: datetime = Field(..., description="End date for the report period")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters to apply to the report")
    group_by: Optional[str] = Field(None, description="Optional field to group results by")


class ReportResponse(BaseModel):
    """
    Custom report generation response.
    
    Contains generated report data with metadata
    and optional export functionality.
    """
    report_id: UUID = Field(..., description="Unique identifier for the generated report")
    report_type: str = Field(..., description="Type of report that was generated")
    generated_at: datetime = Field(..., description="Timestamp when the report was generated")
    data: Dict[str, Any] = Field(..., description="Report data and results")
    export_url: Optional[str] = Field(None, description="URL to download/export the report")


class CustomReportRequest(ReportRequest):
    """
    Backwards-compatible alias for custom report request schema.
    """


class CustomReportResponse(ReportResponse):
    """
    Backwards-compatible alias for custom report response schema.
    """
