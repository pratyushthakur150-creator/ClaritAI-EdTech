
"""
Attribution analytics schemas for AI EdTech CRM platform.
Handles funnel metrics, source attribution, and speed-to-lead analysis.
"""

from datetime import date, datetime
from typing import Optional, Dict, List, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal


class FunnelMetrics(BaseModel):
    """
    Schema for funnel conversion metrics from visitor to enrollment.
    Tracks the complete customer journey through the sales funnel.
    """

    visitors: int = Field(..., ge=0, description="Total unique visitors from analytics_events where event_type = 'page_view'")
    chatbot_engaged: int = Field(..., ge=0, description="Count of users who initiated chatbot sessions")
    leads_created: int = Field(..., ge=0, description="Total number of leads generated in the period")
    calls_answered: int = Field(..., ge=0, description="Count of call_logs where outcome != 'no_answer'")
    demos_scheduled: int = Field(..., ge=0, description="Total number of demo appointments scheduled")
    demos_attended: int = Field(..., ge=0, description="Number of demos actually attended by prospects")
    enrolled: int = Field(..., ge=0, description="Final enrollment count - successful conversions")
    conversion_rate: float = Field(..., ge=0.0, le=1.0, description="Overall conversion rate: enrolled / visitors")

    @field_validator('conversion_rate')
    @classmethod
    def validate_conversion_rate(cls, v: float, info) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError('Conversion rate must be between 0.0 and 1.0')
        return v

    @model_validator(mode='after')
    def validate_funnel_logic(self):
        if self.demos_attended > self.demos_scheduled:
            raise ValueError('Demos attended cannot exceed demos scheduled')
        if self.enrolled > self.leads_created:
            raise ValueError('Enrollments cannot exceed leads created')
        if self.chatbot_engaged > self.visitors:
            raise ValueError('Chatbot engaged cannot exceed total visitors')

        if self.visitors > 0:
            calculated_rate = self.enrolled / self.visitors
            if abs(calculated_rate - self.conversion_rate) > 0.001:
                raise ValueError(f'Conversion rate mismatch: expected {calculated_rate:.4f}, got {self.conversion_rate:.4f}')
        elif self.conversion_rate != 0.0:
            raise ValueError('Conversion rate must be 0.0 when visitors is 0')

        return self

    model_config = {
        "json_encoders": {datetime: lambda dt: dt.isoformat(), date: lambda d: d.isoformat()},
        "from_attributes": True,
        "validate_assignment": True,
        "str_strip_whitespace": True
    }


class SourceAttribution(BaseModel):
    """
    Schema for lead source attribution and conversion analysis.
    Tracks performance by traffic source and marketing channel.
    """

    source: Literal["chatbot", "organic", "paid", "referral", "direct", "social", "email"] = Field(
        ..., description="Lead generation source channel"
    )
    leads: int = Field(..., ge=0, description="Number of leads generated from this source")
    demos: int = Field(..., ge=0, description="Number of demos scheduled from this source")
    enrollments: int = Field(..., ge=0, description="Number of successful enrollments from this source")
    conversion_rate: float = Field(..., ge=0.0, le=1.0, description="Source conversion rate: enrollments / leads")
    avg_time_to_enrollment_days: float = Field(..., ge=0.0, description="Average days from lead creation to enrollment")

    @field_validator('conversion_rate')
    @classmethod
    def validate_conversion_rate(cls, v: float, info) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError('Conversion rate must be between 0.0 and 1.0')
        return v

    @model_validator(mode='after')
    def validate_source_metrics(self):
        if self.demos > self.leads:
            raise ValueError(f'Demos ({self.demos}) cannot exceed leads ({self.leads}) for source {self.source}')
        if self.enrollments > self.leads:
            raise ValueError(f'Enrollments ({self.enrollments}) cannot exceed leads ({self.leads}) for source {self.source}')
        if self.enrollments > self.demos:
            raise ValueError(f'Enrollments ({self.enrollments}) cannot exceed demos ({self.demos}) for source {self.source}')

        if self.leads > 0:
            calculated_rate = self.enrollments / self.leads
            if abs(calculated_rate - self.conversion_rate) > 0.001:
                raise ValueError(f'Conversion rate mismatch for {self.source}: expected {calculated_rate:.4f}, got {self.conversion_rate:.4f}')
        elif self.conversion_rate != 0.0:
            raise ValueError(f'Conversion rate must be 0.0 when leads is 0 for source {self.source}')

        return self

    model_config = {
        "json_encoders": {datetime: lambda dt: dt.isoformat(), date: lambda d: d.isoformat()},
        "from_attributes": True,
        "validate_assignment": True,
        "str_strip_whitespace": True
    }


class SpeedToLeadMetrics(BaseModel):
    """Sub-schema for speed-to-lead analysis metrics per time bucket."""

    leads: int = Field(..., ge=0, description="Number of leads in this response time bucket")
    demos: int = Field(..., ge=0, description="Number of demos scheduled from these leads")
    enrollments: int = Field(..., ge=0, description="Number of enrollments from these leads")
    conversion_rate: float = Field(..., ge=0.0, le=1.0, description="Conversion rate for this time bucket")

    @field_validator('conversion_rate')
    @classmethod
    def validate_conversion_rate(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError('Conversion rate must be between 0.0 and 1.0')
        return v

    @model_validator(mode='after')
    def validate_metrics_consistency(self):
        if self.demos > self.leads:
            raise ValueError('Demos cannot exceed leads in time bucket')
        if self.enrollments > self.leads:
            raise ValueError('Enrollments cannot exceed leads in time bucket')
        if self.enrollments > self.demos:
            raise ValueError('Enrollments cannot exceed demos in time bucket')

        if self.leads > 0:
            calculated_rate = self.enrollments / self.leads
            if abs(calculated_rate - self.conversion_rate) > 0.001:
                raise ValueError(f'Conversion rate mismatch: expected {calculated_rate:.4f}, got {self.conversion_rate:.4f}')
        elif self.conversion_rate != 0.0:
            raise ValueError('Conversion rate must be 0.0 when leads is 0')

        return self


class SpeedToLeadAnalysis(BaseModel):
    """
    Schema for speed-to-lead response time analysis.
    Analyzes conversion impact based on lead response time buckets.
    """

    within_5_min: SpeedToLeadMetrics = Field(..., description="Metrics for leads responded to within 5 minutes")
    within_30_min: SpeedToLeadMetrics = Field(..., description="Metrics for leads responded to within 30 minutes")
    over_30_min: SpeedToLeadMetrics = Field(..., description="Metrics for leads responded to after 30 minutes")
    impact_summary: str = Field(..., min_length=10, max_length=500, description="Summary of response time impact on conversions")

    @field_validator('impact_summary')
    @classmethod
    def validate_impact_summary(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError('Impact summary must be at least 10 characters long')
        if not any(word in v.lower() for word in ['conversion', 'impact', 'response', 'time', 'performance']):
            raise ValueError('Impact summary should describe conversion or performance impact')
        return v

    model_config = {
        "json_encoders": {datetime: lambda dt: dt.isoformat(), date: lambda d: d.isoformat()},
        "from_attributes": True,
        "validate_assignment": True,
        "str_strip_whitespace": True
    }


# FIX: Added ResponseTimeBucket and SpeedImpactSummary aliases
# that attribution_service.py imports
ResponseTimeBucket = SpeedToLeadMetrics
SpeedImpactSummary = SpeedToLeadAnalysis


class AttributionDateRange(BaseModel):
    """Schema for date range filtering in attribution analytics requests."""

    start_date: Optional[date] = Field(None, description="Start date for attribution analysis (ISO format: YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="End date for attribution analysis (ISO format: YYYY-MM-DD)")

    @model_validator(mode='after')
    def validate_date_range(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError('Start date must be before or equal to end date')
            days_diff = (self.end_date - self.start_date).days
            if days_diff > 730:
                raise ValueError('Date range cannot exceed 2 years')
        return self

    model_config = {
        "json_encoders": {date: lambda d: d.isoformat()},
        "from_attributes": True,
        "validate_assignment": True
    }


class AttributionRequest(BaseModel):
    """Schema for attribution analytics API requests."""

    date_range: Optional[AttributionDateRange] = Field(None, description="Date range filter for the analysis")
    sources: Optional[List[str]] = Field(None, description="Specific sources to analyze")
    include_funnel: bool = Field(True, description="Whether to include funnel metrics in response")
    include_sources: bool = Field(True, description="Whether to include source attribution in response")
    include_speed_analysis: bool = Field(True, description="Whether to include speed-to-lead analysis in response")

    @field_validator('sources')
    @classmethod
    def validate_sources(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            valid_sources = {"chatbot", "organic", "paid", "referral", "direct", "social", "email"}
            invalid_sources = set(v) - valid_sources
            if invalid_sources:
                raise ValueError(f'Invalid sources: {invalid_sources}. Valid sources: {valid_sources}')
        return v

    model_config = {
        "json_encoders": {date: lambda d: d.isoformat()},
        "from_attributes": True,
        "validate_assignment": True,
        "str_strip_whitespace": True
    }


class AttributionMetadata(BaseModel):
    """Schema for attribution analytics response metadata."""

    total_records: int = Field(..., ge=0, description="Total number of records analyzed")
    date_range: Optional[AttributionDateRange] = Field(None, description="Actual date range used in the analysis")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Filters that were applied")
    analysis_timestamp: datetime = Field(..., description="When this analysis was generated")
    data_freshness: str = Field(..., description="How fresh the analyzed data is")

    model_config = {
        "json_encoders": {datetime: lambda dt: dt.isoformat(), date: lambda d: d.isoformat()},
        "from_attributes": True,
        "validate_assignment": True,
        "str_strip_whitespace": True
    }


class AttributionAnalyticsResponse(BaseModel):
    """Complete schema for attribution analytics API response."""

    funnel_metrics: Optional[FunnelMetrics] = Field(None, description="Overall funnel conversion metrics")
    source_attribution: Optional[List[SourceAttribution]] = Field(None, description="Attribution metrics by source")
    speed_to_lead_analysis: Optional[SpeedToLeadAnalysis] = Field(None, description="Analysis of conversion impact by response time")
    metadata: AttributionMetadata = Field(..., description="Response metadata including filters and timestamps")

    @model_validator(mode='after')
    def validate_response_content(self):
        if not any([self.funnel_metrics, self.source_attribution, self.speed_to_lead_analysis]):
            raise ValueError('At least one analytics section must be included in the response')
        return self

    model_config = {
        "json_encoders": {datetime: lambda dt: dt.isoformat(), date: lambda d: d.isoformat()},
        "from_attributes": True,
        "validate_assignment": True,
        "str_strip_whitespace": True,
        "use_enum_values": True
    }