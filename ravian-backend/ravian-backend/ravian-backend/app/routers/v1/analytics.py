"""
Analytics API Router

This module contains all FastAPI endpoints for analytics and reporting functionality.
Provides comprehensive analytics data including dashboard metrics, conversion funnels,
team performance, revenue analytics, and custom reports with proper authentication
and multi-tenant security.

Endpoints:
- GET /analytics/dashboard: Core dashboard KPIs and metrics
- GET /analytics/funnel: Conversion funnel analysis  
- GET /analytics/team-performance: Agent and team performance metrics
- GET /analytics/revenue: Revenue analytics and forecasting
- POST /analytics/reports: Custom report generation
- GET /analytics/health: Service health check
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

# Database and authentication imports
from app.core.database import get_db_session
from app.core.utils import get_tenant_id
from app.dependencies.auth import get_current_user

# Schema imports from analytics module
from app.schemas.analytics import (
    DashboardOverviewResponse,
    ConversionFunnelResponse,
    TeamPerformanceResponse,
    RevenueAnalyticsResponse,
    ReportRequest,
    ReportResponse
)

# Service import
from app.services.analytics_service import AnalyticsService

# Create router instance
router = APIRouter(
    prefix="/analytics",
    tags=["Analytics & Reporting"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


@router.get(
    "/dashboard",
    response_model=DashboardOverviewResponse,
    summary="Get Dashboard Overview",
    description="""
    Retrieve comprehensive dashboard metrics including total leads, conversions,
    revenue, and key performance indicators with trend analysis.
    
    **Authentication Required:** Yes
    
    **Parameters:**
    - date_from: Start date for metrics (defaults to 30 days ago)
    - date_to: End date for metrics (defaults to current date)
    
    **Returns:**
    - Dashboard metrics with KPIs, trends, top courses, and recent activities
    - Conversion rates, attendance rates, and revenue metrics
    - Period-over-period trend analysis
    
    **Example:**
    GET /analytics/dashboard?date_from=2024-01-01&date_to=2024-01-31
    """
)
async def get_dashboard_overview(
    date_from: Optional[datetime] = Query(
        default=None,
        description="Start date for dashboard metrics (ISO format: YYYY-MM-DDTHH:MM:SS)"
    ),
    date_to: Optional[datetime] = Query(
        default=None,
        description="End date for dashboard metrics (ISO format: YYYY-MM-DDTHH:MM:SS)"
    ),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get comprehensive dashboard overview with KPIs and trends.
    
    Provides core business metrics including lead counts, conversion rates,
    revenue figures, and trend analysis compared to previous periods.
    Multi-tenant secure with proper authentication.
    """
    try:
        # Set default date range (last 30 days) if not provided
        if date_to is None:
            date_to = datetime.now()
        if date_from is None:
            date_from = date_to - timedelta(days=30)
            
        # Extract tenant_id from authenticated user
        tenant_id = get_tenant_id(current_user)
        
        # Initialize analytics service
        analytics_service = AnalyticsService(db)
        
        # Get dashboard data
        dashboard_data = await analytics_service.get_dashboard_overview(
            tenant_id=tenant_id,
            date_from=date_from,
            date_to=date_to
        )
        
        return dashboard_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format or tenant ID: {str(e)}"
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Dashboard analytics error: {e}", exc_info=True)
        # Return safe defaults instead of 500 error so the frontend still renders
        return {
            "metrics": {
                "total_leads": 0,
                "active_leads": 0,
                "converted_leads": 0,
                "total_calls": 0,
                "total_demos": 0,
                "total_enrollments": 0,
                "revenue": 0.0,
                "conversion_rate": 0.0,
                "demo_attendance_rate": 0.0,
                "call_answer_rate": 0.0,
                "period_start": date_from,
                "period_end": date_to
            },
            "trends": {},
            "top_courses": [],
            "recent_activities": []
        }


@router.get(
    "/funnel",
    response_model=ConversionFunnelResponse,
    summary="Get Conversion Funnel Analysis",
    description="""
    Analyze the lead conversion funnel with stage-by-stage breakdown,
    conversion rates, and bottleneck identification.
    
    **Authentication Required:** Yes
    
    **Parameters:**
    - date_from: Start date for funnel analysis (defaults to 30 days ago)
    - date_to: End date for funnel analysis (defaults to current date)
    
    **Returns:**
    - Funnel stages with counts and conversion rates
    - Drop-off rates between stages
    - Overall conversion rate and bottleneck identification
    - Total leads and enrollments summary
    
    **Example:**
    GET /analytics/funnel?date_from=2024-01-01&date_to=2024-01-31
    """
)
async def get_conversion_funnel(
    date_from: Optional[datetime] = Query(
        default=None,
        description="Start date for funnel analysis (ISO format: YYYY-MM-DDTHH:MM:SS)"
    ),
    date_to: Optional[datetime] = Query(
        default=None,
        description="End date for funnel analysis (ISO format: YYYY-MM-DDTHH:MM:SS)"
    ),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get detailed conversion funnel analysis with stage breakdown.
    
    Analyzes lead progression through conversion stages: leads -> contacts ->
    demos -> enrollments with conversion and drop-off rates for each stage.
    Identifies bottleneck stages for optimization opportunities.
    """
    try:
        # Set default date range (last 30 days) if not provided
        if date_to is None:
            date_to = datetime.now()
        if date_from is None:
            date_from = date_to - timedelta(days=30)
            
        # Extract tenant_id from authenticated user
        tenant_id = get_tenant_id(current_user)
        
        # Initialize analytics service
        analytics_service = AnalyticsService(db)
        
        # Get funnel data
        funnel_data = await analytics_service.get_conversion_funnel(
            tenant_id=tenant_id,
            date_from=date_from,
            date_to=date_to
        )
        
        return funnel_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format or tenant ID: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversion funnel: {str(e)}"
        )


@router.get(
    "/team-performance",
    response_model=TeamPerformanceResponse,
    summary="Get Team Performance Metrics",
    description="""
    Retrieve comprehensive team and individual agent performance metrics
    including calls, demos, enrollments, and conversion rates.
    
    **Authentication Required:** Yes
    
    **Parameters:**
    - date_from: Start date for performance metrics (defaults to 30 days ago)
    - date_to: End date for performance metrics (defaults to current date)
    
    **Returns:**
    - Individual agent performance metrics
    - Team averages and totals
    - Top performer identification
    - Call statistics and satisfaction scores
    
    **Example:**
    GET /analytics/team-performance?date_from=2024-01-01&date_to=2024-01-31
    """
)
async def get_team_performance(
    date_from: Optional[datetime] = Query(
        default=None,
        description="Start date for team performance (ISO format: YYYY-MM-DDTHH:MM:SS)"
    ),
    date_to: Optional[datetime] = Query(
        default=None,
        description="End date for team performance (ISO format: YYYY-MM-DDTHH:MM:SS)"
    ),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get comprehensive team and agent performance analytics.
    
    Provides individual agent metrics including calls made, demos conducted,
    enrollments generated, conversion rates, and satisfaction scores.
    Includes team averages and top performer identification.
    """
    try:
        # Set default date range (last 30 days) if not provided
        if date_to is None:
            date_to = datetime.now()
        if date_from is None:
            date_from = date_to - timedelta(days=30)
            
        # Extract tenant_id from authenticated user
        tenant_id = get_tenant_id(current_user)
        
        # Initialize analytics service
        analytics_service = AnalyticsService(db)
        
        # Get team performance data
        performance_data = await analytics_service.get_team_performance(
            tenant_id=tenant_id,
            date_from=date_from,
            date_to=date_to
        )
        
        return performance_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format or tenant ID: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve team performance: {str(e)}"
        )


@router.get(
    "/revenue",
    response_model=RevenueAnalyticsResponse,
    summary="Get Revenue Analytics",
    description="""
    Comprehensive revenue analysis including total revenue, course breakdown,
    monthly trends, and forecasting with growth rate calculations.
    
    **Authentication Required:** Yes
    
    **Parameters:**
    - date_from: Start date for revenue analysis (defaults to 30 days ago)
    - date_to: End date for revenue analysis (defaults to current date)
    
    **Returns:**
    - Total revenue and growth rates
    - Revenue breakdown by course
    - Monthly revenue time series
    - Next month revenue forecast
    - Average revenue per student metrics
    
    **Example:**
    GET /analytics/revenue?date_from=2024-01-01&date_to=2024-01-31
    """
)
async def get_revenue_analytics(
    date_from: Optional[datetime] = Query(
        default=None,
        description="Start date for revenue analysis (ISO format: YYYY-MM-DDTHH:MM:SS)"
    ),
    date_to: Optional[datetime] = Query(
        default=None,
        description="End date for revenue analysis (ISO format: YYYY-MM-DDTHH:MM:SS)"
    ),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get comprehensive revenue analytics with forecasting.
    
    Analyzes revenue performance including total revenue, course-wise breakdown,
    monthly trends, growth rates, and predictive forecasting for next month.
    Includes average revenue per student calculations.
    """
    try:
        # Set default date range (last 30 days) if not provided
        if date_to is None:
            date_to = datetime.now()
        if date_from is None:
            date_from = date_to - timedelta(days=30)
            
        # Extract tenant_id from authenticated user
        tenant_id = get_tenant_id(current_user)
        
        # Initialize analytics service
        analytics_service = AnalyticsService(db)
        
        # Get revenue analytics data
        revenue_data = await analytics_service.get_revenue_analytics(
            tenant_id=tenant_id,
            date_from=date_from,
            date_to=date_to
        )
        
        return revenue_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format or tenant ID: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve revenue analytics: {str(e)}"
        )


@router.post(
    "/reports",
    response_model=ReportResponse,
    summary="Generate Custom Report",
    description="""
    Generate custom analytics reports based on specified parameters,
    filters, and grouping options with exportable output.
    
    **Authentication Required:** Yes
    
    **Request Body:** ReportRequest with:
    - report_type: Type of report to generate
    - date_from: Start date for report data
    - date_to: End date for report data
    - filters: Optional filtering criteria
    - group_by: Optional grouping parameter
    
    **Returns:**
    - Generated report with unique ID
    - Report data and metadata
    - Export URL for downloading
    - Generation timestamp
    
    **Example Request Body:**
    {
        "report_type": "dashboard",
        "date_from": "2024-01-01T00:00:00",
        "date_to": "2024-01-31T23:59:59",
        "filters": {"course_id": "12345"},
        "group_by": "course"
    }
    """
)
async def generate_custom_report(
    report_request: ReportRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Generate custom analytics report based on request parameters.
    
    Creates customized reports with specified date ranges, filters,
    and grouping options. Returns report data with unique ID and
    optional export URL for downloading processed reports.
    """
    try:
        # Extract tenant_id from authenticated user
        tenant_id = get_tenant_id(current_user)
        
        # Initialize analytics service
        analytics_service = AnalyticsService(db)
        
        # Generate custom report
        report_data = await analytics_service.generate_custom_report(
            tenant_id=tenant_id,
            report_type=report_request.report_type,
            date_from=report_request.date_from,
            date_to=report_request.date_to,
            filters=report_request.filters
        )
        
        return report_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid report request or tenant ID: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate custom report: {str(e)}"
        )


@router.get("/students")
async def get_student_analytics(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get student analytics - returns real data from enrollments, students, and courses"""
    try:
        from app.models.enrollment import Enrollment, Student
        from app.models.teaching import Course
        from app.models.lead import Lead
        from sqlalchemy import func
        import uuid

        tenant_id = get_tenant_id(current_user)

        # --- Build riskStudents from Student model ---
        students = db.query(Student).filter(
            Student.tenant_id == tenant_id,
            Student.is_deleted == False
        ).all()

        risk_students = []
        for s in students:
            # Get the related enrollment and course name
            enrollment = db.query(Enrollment).filter(
                Enrollment.id == s.enrollment_id,
                Enrollment.is_deleted == False
            ).first()

            course_name = "Unknown Course"
            if enrollment and enrollment.course_id:
                course = db.query(Course).filter(Course.id == enrollment.course_id).first()
                if course:
                    course_name = course.name

            # Get student name from lead
            student_name = "Unknown Student"
            if s.lead_id:
                lead = db.query(Lead).filter(Lead.id == s.lead_id).first()
                if lead:
                    student_name = lead.name or lead.email or "Unknown Student"

            # Map risk_level enum to display text
            risk_level_str = getattr(s.risk_level, 'value', str(s.risk_level)) if s.risk_level else 'low'
            risk_display = {
                'critical': 'High Risk',
                'high': 'High Risk',
                'medium': 'Medium Risk',
                'low': 'Low Risk'
            }.get(risk_level_str, 'Low Risk')

            # Calculate modules behind
            modules_behind = max(0, (s.modules_total or 0) - (s.modules_completed or 0))

            # Calculate attendance-like metric from engagement_score
            attendance = s.engagement_score or 0

            risk_students.append({
                "id": str(s.id),
                "name": student_name,
                "course": course_name,
                "riskLevel": risk_display,
                "modulesBehind": modules_behind,
                "attendance": attendance,
                "lastActive": s.last_active.isoformat() if s.last_active else s.created_at.isoformat()
            })

        # --- Build heatmap from courses with enrolled students ---
        courses = db.query(Course).filter(
            Course.tenant_id == tenant_id,
            Course.is_deleted == False
        ).all()

        heatmap = []
        for course in courses:
            # Count students enrolled in this course
            course_enrollments = db.query(Enrollment).filter(
                Enrollment.course_id == course.id,
                Enrollment.tenant_id == tenant_id,
                Enrollment.is_deleted == False
            ).all()

            enrollment_ids = [e.id for e in course_enrollments]
            if not enrollment_ids:
                continue

            course_students = db.query(Student).filter(
                Student.enrollment_id.in_(enrollment_ids),
                Student.is_deleted == False
            ).all()

            if not course_students:
                continue

            # Calculate confusion level from average completion (lower completion = higher confusion)
            avg_completion = sum(float(s.completion_percentage or 0) for s in course_students) / len(course_students)
            confusion_level = max(0, min(100, int(100 - avg_completion)))

            heatmap.append({
                "moduleId": str(course.id),
                "moduleName": course.name,
                "confusionLevel": confusion_level,
                "studentCount": len(course_students)
            })

        # --- Build confusions from student current_module data ---
        confusions = []
        module_confusion_counts = {}
        for s in students:
            if s.current_module:
                key = s.current_module
                if key not in module_confusion_counts:
                    module_confusion_counts[key] = {
                        "count": 0,
                        "lastOccurred": s.last_active or s.created_at
                    }
                module_confusion_counts[key]["count"] += 1
                student_time = s.last_active or s.created_at
                if student_time and student_time > module_confusion_counts[key]["lastOccurred"]:
                    module_confusion_counts[key]["lastOccurred"] = student_time

        for idx, (module_name, data) in enumerate(module_confusion_counts.items()):
            confusions.append({
                "id": f"c{idx+1}",
                "topic": f"Progress stalled in {module_name}",
                "module": module_name,
                "count": data["count"],
                "lastOccurred": data["lastOccurred"].isoformat() if data["lastOccurred"] else None
            })

        # Sort confusions by count descending
        confusions.sort(key=lambda x: x["count"], reverse=True)

        return {
            "total_students": len(students),
            "total_enrollments": db.query(Enrollment).filter(
                Enrollment.tenant_id == tenant_id,
                Enrollment.is_deleted == False
            ).count(),
            "active_students": len(students),
            "completion_rate": 0,
            "riskStudents": risk_students,
            "heatmap": heatmap,
            "confusions": confusions[:10],  # Top 10
            "status": "success"
        }
    except Exception as e:
        import traceback
        logging.getLogger(__name__).error(f"Student analytics error: {traceback.format_exc()}")
        return {
            "total_students": 0,
            "total_enrollments": 0,
            "active_students": 0,
            "completion_rate": 0,
            "riskStudents": [],
            "heatmap": [],
            "confusions": [],
            "status": "fallback",
            "error": str(e)
        }


@router.get("/overview")
async def get_analytics_overview(
    days: int = Query(default=30, description="Number of days to analyze"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get overall analytics overview with chart data"""
    try:
        from app.models.lead import Lead, LeadSource
        from app.models.enrollment import Enrollment
        from app.models.enrollment import Student
        from app.models.teaching import Course
        from sqlalchemy import func, extract, case, cast, String as SAString
        import calendar

        tenant_id = get_tenant_id(current_user)
        date_to = datetime.now()
        date_from = date_to - timedelta(days=days)

        # ── KPI cards (existing) ──────────────────────────────────────
        total_leads = db.query(Lead).filter(
            Lead.tenant_id == tenant_id,
            Lead.is_deleted == False
        ).count()

        active_students = db.query(Student).filter(
            Student.tenant_id == tenant_id,
            Student.is_deleted == False
        ).count()

        conversions = db.query(Enrollment).filter(
            Enrollment.tenant_id == tenant_id,
            Enrollment.is_deleted == False
        ).count()

        revenue = db.query(func.coalesce(func.sum(Enrollment.total_amount), 0)).filter(
            Enrollment.tenant_id == tenant_id,
            Enrollment.is_deleted == False,
            Enrollment.enrolled_at >= date_from,
            Enrollment.enrolled_at <= date_to
        ).scalar() or 0

        # ── Leads over time (daily for short range, monthly for long) ───
        leads_over_time = []
        try:
            from sqlalchemy import cast, Date

            if days <= 31:
                # Daily buckets: one point per day so the line chart shows a trend
                daily_leads = (
                    db.query(
                        cast(Lead.created_at, Date).label('d'),
                        func.count(Lead.id).label('cnt')
                    )
                    .filter(
                        Lead.tenant_id == tenant_id,
                        Lead.is_deleted == False,
                        Lead.created_at >= date_from,
                        Lead.created_at <= date_to
                    )
                    .group_by(cast(Lead.created_at, Date))
                    .all()
                )
                count_by_date = {row.d: row.cnt for row in daily_leads}
                # Fill every day in range so the chart has a point per day
                one_day = timedelta(days=1)
                current = date_from.date() if hasattr(date_from, 'date') else date_from
                end_date = date_to.date() if hasattr(date_to, 'date') else date_to
                while current <= end_date:
                    day_label = f"{calendar.month_abbr[current.month]} {current.day}"
                    leads_over_time.append({
                        "name": day_label,
                        "leads": count_by_date.get(current, 0)
                    })
                    current = current + one_day
            else:
                # Monthly buckets for longer ranges
                monthly_leads = (
                    db.query(
                        extract('year', Lead.created_at).label('yr'),
                        extract('month', Lead.created_at).label('mo'),
                        func.count(Lead.id).label('cnt')
                    )
                    .filter(
                        Lead.tenant_id == tenant_id,
                        Lead.is_deleted == False,
                        Lead.created_at >= date_from,
                        Lead.created_at <= date_to
                    )
                    .group_by(extract('year', Lead.created_at), extract('month', Lead.created_at))
                    .order_by('yr', 'mo')
                    .all()
                )
                for row in monthly_leads:
                    month_name = calendar.month_abbr[int(row.mo)]
                    leads_over_time.append({
                        "name": f"{month_name} {int(row.yr)}",
                        "leads": row.cnt
                    })
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"leads_over_time query failed: {e}")

        # ── Lead sources (pie chart) ──────────────────────────────────
        lead_sources = []
        SOURCE_COLORS = {
            "WEBSITE": "#3b82f6",
            "CHATBOT": "#10b981",
            "REFERRAL": "#f59e0b",
            "SOCIAL_MEDIA": "#8b5cf6",
            "ADVERTISING": "#ef4444",
            "EMAIL_CAMPAIGN": "#06b6d4",
            "DIRECT": "#ec4899",
            "OTHER": "#6b7280",
        }
        try:
            source_rows = (
                db.query(
                    Lead.source,
                    func.count(Lead.id).label('cnt')
                )
                .filter(
                    Lead.tenant_id == tenant_id,
                    Lead.is_deleted == False,
                    Lead.created_at >= date_from,
                    Lead.created_at <= date_to
                )
                .group_by(Lead.source)
                .order_by(func.count(Lead.id).desc())
                .all()
            )
            for row in source_rows:
                source_val = row.source.value if hasattr(row.source, 'value') else str(row.source)
                lead_sources.append({
                    "name": source_val.replace("_", " ").title(),
                    "value": row.cnt,
                    "color": SOURCE_COLORS.get(source_val, "#6b7280")
                })
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"lead_sources query failed: {e}")

        # ── Courses popularity (bar chart) ────────────────────────────
        courses_popularity = []
        try:
            course_rows = (
                db.query(
                    Course.name,
                    func.count(Enrollment.id).label('students')
                )
                .join(Enrollment, Enrollment.course_id == Course.id)
                .filter(
                    Enrollment.tenant_id == tenant_id,
                    Enrollment.is_deleted == False,
                )
                .group_by(Course.name)
                .order_by(func.count(Enrollment.id).desc())
                .limit(10)
                .all()
            )
            for row in course_rows:
                courses_popularity.append({
                    "name": row.name,
                    "students": row.students
                })
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"courses_popularity query failed: {e}")

        return {
            "total_leads": total_leads,
            "conversions": conversions,
            "active_students": active_students,
            "revenue": float(revenue),
            "conversion_rate": round((conversions / total_leads * 100) if total_leads > 0 else 0, 2),
            "leads_over_time": leads_over_time,
            "lead_sources": lead_sources,
            "courses_popularity": courses_popularity,
            "status": "success"
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Analytics overview error: {e}", exc_info=True)
        return {
            "total_leads": 0,
            "conversions": 0,
            "active_students": 0,
            "revenue": 0,
            "conversion_rate": 0,
            "leads_over_time": [],
            "lead_sources": [],
            "courses_popularity": [],
            "status": "fallback"
        }


@router.get(
    "/health",
    summary="Analytics Service Health Check",
    description="""
    Check the health and availability of the analytics service.
    No authentication required for monitoring purposes.
    
    **Authentication Required:** No
    
    **Returns:**
    - Service status and timestamp
    - Basic system health indicators
    - Version information
    
    **Example:**
    GET /analytics/health
    """
)
async def health_check():
    """
    Health check endpoint for analytics service monitoring.
    
    Provides basic health status without authentication requirements
    for monitoring systems and load balancers to verify service availability.
    """
    try:
        return {
            "status": "healthy",
            "service": "analytics",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "endpoints": [
                "dashboard",
                "funnel", 
                "team-performance",
                "revenue",
                "reports"
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )
