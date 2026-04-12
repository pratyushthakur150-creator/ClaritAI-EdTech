"""
Attribution service for AI EdTech CRM platform.
Handles funnel metrics, source attribution, and speed-to-lead analysis.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, case, extract

# Import attribution schemas
from app.schemas.attribution import (
    FunnelMetrics,
    SourceAttribution,
    SpeedToLeadAnalysis,
    ResponseTimeBucket,
    SpeedImpactSummary
)

# FIX: Corrected model imports to match your actual project structure
from app.models.lead import Lead           # was: app.models.leads
from app.models.call import CallLog, CallOutcome  # CallLog model and CallOutcome enum
from app.models.call import Demo           # Demo lives in call.py in your project
from app.models.enrollment import Enrollment
from app.models.analytics import AnalyticsEvent, EventType

logger = logging.getLogger(__name__)


class AttributionService:
    """Service class for handling attribution analysis and funnel metrics."""

    def __init__(self, db: Session):
        """Initialize attribution service with database session."""
        self.db = db

    def get_funnel_metrics(
        self,
        tenant_id: UUID,
        date_range: Tuple[datetime, datetime]
    ) -> FunnelMetrics:
        """Calculate funnel metrics."""
        try:
            date_from, date_to = date_range
            
            # 1. Visitors - count distinct user sessions from any analytics event
            visitors = self.db.query(func.count(func.distinct(AnalyticsEvent.session_id))).filter(
                and_(
                    AnalyticsEvent.tenant_id == tenant_id,
                    AnalyticsEvent.created_at >= date_from,
                    AnalyticsEvent.created_at <= date_to
                )
            ).scalar() or 0
            
            # 2. Chatbot engaged - users who started chatbot sessions
            chatbot_engaged = self.db.query(func.count(func.distinct(AnalyticsEvent.session_id))).filter(
                and_(
                    AnalyticsEvent.tenant_id == tenant_id,
                    AnalyticsEvent.event_type == EventType.CHATBOT_SESSION_START,
                    AnalyticsEvent.created_at >= date_from,
                    AnalyticsEvent.created_at <= date_to
                )
            ).scalar() or 0
            
            # 3. Leads created - from Lead table
            leads_created = self.db.query(func.count(Lead.id)).filter(
                and_(
                    Lead.tenant_id == tenant_id,
                    Lead.created_at >= date_from,
                    Lead.created_at <= date_to
                )
            ).scalar() or 0
            
            # 4. Calls answered - JOIN CallLog with Lead to filter by tenant
            calls_answered = (
                self.db.query(func.count(CallLog.id))
                .join(Lead, CallLog.lead_id == Lead.id)
                .filter(
                    and_(
                        Lead.tenant_id == tenant_id,
                        CallLog.outcome != CallOutcome.NO_ANSWER,
                        CallLog.created_at >= date_from,
                        CallLog.created_at <= date_to
                    )
                )
                .scalar() or 0
            )
            
            # 5. Demos scheduled - from Demo table
            demos_scheduled = self.db.query(func.count(Demo.id)).filter(
                and_(
                    Demo.tenant_id == tenant_id,
                    Demo.created_at >= date_from,
                    Demo.created_at <= date_to
                )
            ).scalar() or 0
            
            # 6. Demos attended - demos with status 'completed' or 'attended'
            demos_attended = self.db.query(func.count(Demo.id)).filter(
                and_(
                    Demo.tenant_id == tenant_id,
                    or_(Demo.completed == True, Demo.attended == True),
                    Demo.created_at >= date_from,
                    Demo.created_at <= date_to
                )
            ).scalar() or 0
            
            # 7. Enrolled - from Enrollment table
            enrolled = self.db.query(func.count(Enrollment.id)).filter(
                and_(
                    Enrollment.tenant_id == tenant_id,
                    Enrollment.created_at >= date_from,
                    Enrollment.created_at <= date_to
                )
            ).scalar() or 0
            
            # 8. Calculate conversion rate
            conversion_rate = (enrolled / visitors) if visitors > 0 else 0.0
            
            return FunnelMetrics(
                visitors=visitors,
                chatbot_engaged=chatbot_engaged,
                leads_created=leads_created,
                calls_answered=calls_answered,
                demos_scheduled=demos_scheduled,
                demos_attended=demos_attended,
                enrolled=enrolled,
                conversion_rate=conversion_rate
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate funnel metrics: {e}")
            raise

    def get_source_attribution(
        self,
        tenant_id: UUID,
        date_range: Tuple[datetime, datetime],
        source_filter: Optional[List[str]] = None
    ) -> List[SourceAttribution]:
        """
        Analyze attribution by lead source with conversion rates and time to enrollment.
        """
        try:
            start_date, end_date = date_range
            logger.info(f"Computing source attribution for tenant {tenant_id}")

            # Query leads grouped by source with conversion data
            query = (
                self.db.query(
                    Lead.source,
                    func.count(Lead.id).label('leads_count'),
                    func.count(Demo.id).label('demos_count'),
                    func.count(Enrollment.id).label('enrollments_count'),
                    func.avg(
                        func.extract('epoch', Enrollment.enrolled_at - Lead.created_at) / 86400
                    ).label('avg_time_to_enrollment_days')
                )
                .outerjoin(Demo, Lead.id == Demo.lead_id)
                .outerjoin(Enrollment, Lead.id == Enrollment.lead_id)
                .filter(
                    and_(
                        Lead.tenant_id == tenant_id,
                        Lead.created_at >= start_date,
                        Lead.created_at <= end_date
                    )
                )
                .group_by(Lead.source)
            )

            # Apply source filter if provided
            if source_filter:
                query = query.filter(Lead.source.in_(source_filter))

            source_query = query.all()

            source_attributions = []

            # Valid sources that match schema Literal type
            valid_sources = {"chatbot", "organic", "paid", "referral", "direct", "social", "email"}

            for row in source_query:
                # FIX: Normalize source to match schema Literal values
                source = (row.source or 'direct').lower()
                if source not in valid_sources:
                    source = 'direct'  # Default fallback

                leads_count = row.leads_count or 0
                demos_count = row.demos_count or 0
                enrollments_count = row.enrollments_count or 0
                avg_time_to_enrollment = row.avg_time_to_enrollment_days or 0.0

                # FIX: conversion_rate as fraction 0.0-1.0 to match schema
                conversion_rate = (enrollments_count / leads_count) if leads_count > 0 else 0.0

                # FIX: Use correct schema field names (leads/demos/enrollments not leads_count etc.)
                source_attribution = SourceAttribution(
                    source=source,
                    leads=leads_count,
                    demos=demos_count,
                    enrollments=enrollments_count,
                    conversion_rate=round(conversion_rate, 4),
                    avg_time_to_enrollment_days=round(float(avg_time_to_enrollment), 1)
                )

                source_attributions.append(source_attribution)

            source_attributions.sort(key=lambda x: x.conversion_rate, reverse=True)
            return source_attributions

        except Exception as e:
            logger.error(f"Failed to calculate source attribution for tenant {tenant_id}: {e}")
            raise

    def get_speed_to_lead_analysis(
        self,
        tenant_id: UUID,
        date_range: Tuple[datetime, datetime]
    ) -> SpeedToLeadAnalysis:
        """
        Analyze the impact of response speed on lead conversion.
        """
        try:
            start_date, end_date = date_range
            logger.info(f"Analyzing speed to lead for tenant {tenant_id}")

            # Build subquery for leads with first call times
            # FIX: Use CallLog model (not Call)
            leads_with_calls_query = (
                self.db.query(
                    Lead.id.label('lead_id'),
                    Lead.created_at.label('lead_created_at'),
                    func.min(CallLog.created_at).label('first_call_at')
                )
                .join(CallLog, Lead.id == CallLog.lead_id)
                .filter(
                    and_(
                        Lead.tenant_id == tenant_id,
                        Lead.created_at >= start_date,
                        Lead.created_at <= end_date
                    )
                )
                .group_by(Lead.id, Lead.created_at)
                .subquery()
            )

            # Calculate response time buckets
            response_time_query = (
                self.db.query(
                    leads_with_calls_query.c.lead_id,
                    case(
                        (func.extract('epoch',
                            leads_with_calls_query.c.first_call_at - leads_with_calls_query.c.lead_created_at
                         ) <= 300, 'under_5_minutes'),
                        (func.extract('epoch',
                            leads_with_calls_query.c.first_call_at - leads_with_calls_query.c.lead_created_at
                         ) <= 1800, '5_to_30_minutes'),
                        else_='over_30_minutes'
                    ).label('response_bucket')
                )
                .subquery()
            )

            # Join with conversion data
            conversion_query = (
                self.db.query(
                    response_time_query.c.response_bucket,
                    func.count(response_time_query.c.lead_id).label('leads_count'),
                    func.count(Demo.id).label('demos_count'),
                    func.count(Enrollment.id).label('enrollments_count')
                )
                .select_from(response_time_query)
                .outerjoin(Demo, response_time_query.c.lead_id == Demo.lead_id)
                .outerjoin(Enrollment, response_time_query.c.lead_id == Enrollment.lead_id)
                .group_by(response_time_query.c.response_bucket)
                .all()
            )

            # Build bucket data dict
            bucket_data = {}

            for row in conversion_query:
                bucket_name = row.response_bucket
                leads_count = row.leads_count or 0
                demos_count = row.demos_count or 0
                enrollments_count = row.enrollments_count or 0

                # FIX: conversion_rate as fraction 0.0-1.0
                conversion_rate = (enrollments_count / leads_count) if leads_count > 0 else 0.0

                # FIX: Use correct SpeedToLeadMetrics field names
                from app.schemas.attribution import SpeedToLeadMetrics
                bucket = SpeedToLeadMetrics(
                    leads=leads_count,
                    demos=demos_count,
                    enrollments=enrollments_count,
                    conversion_rate=round(conversion_rate, 4)
                )
                bucket_data[bucket_name] = bucket

            # Default empty bucket
            from app.schemas.attribution import SpeedToLeadMetrics
            empty_bucket = SpeedToLeadMetrics(
                leads=0, demos=0, enrollments=0, conversion_rate=0.0
            )

            within_5 = bucket_data.get('under_5_minutes', empty_bucket)
            within_30 = bucket_data.get('5_to_30_minutes', empty_bucket)
            over_30 = bucket_data.get('over_30_minutes', empty_bucket)

            # Generate impact summary string
            fast_rate = within_5.conversion_rate * 100
            slow_rate = over_30.conversion_rate * 100
            lift = fast_rate - slow_rate

            if within_5.leads > 0 and over_30.leads > 0:
                impact_summary = (
                    f"Fast response (under 5 min) shows {lift:.1f}% conversion performance "
                    f"vs slow response (over 30 min). Response time has significant impact on conversions."
                )
            else:
                impact_summary = (
                    "Insufficient data to fully analyze response time impact on conversion performance."
                )

            return SpeedToLeadAnalysis(
                within_5_min=within_5,
                within_30_min=within_30,
                over_30_min=over_30,
                impact_summary=impact_summary
            )

        except Exception as e:
            logger.error(f"Failed to analyze speed to lead for tenant {tenant_id}: {e}")
            raise

    def _safe_division(self, numerator: float, denominator: float, default: float = 0.0) -> float:
        """Helper method to safely perform division and avoid division by zero."""
        return numerator / denominator if denominator > 0 else default