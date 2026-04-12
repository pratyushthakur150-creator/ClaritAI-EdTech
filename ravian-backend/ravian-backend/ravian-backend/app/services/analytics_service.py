"""
Analytics Service Module

Provides business logic for analytics operations including dashboard metrics,
conversion funnel analysis, team performance, revenue analytics, and custom reporting.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from sqlalchemy.exc import SQLAlchemyError

# Import database models (assuming these exist)
try:
    from app.models.lead import Lead, LeadStatus
    from app.models.call import CallLog as Call, Demo
    from app.models.enrollment import Enrollment
    # from app.models.agent import Agent  # TODO: Create Agent model - temporarily disabled
    from app.models.teaching import Course
except ImportError as e:
    logging.warning(f"Some database models not available: {e}")
    # Mock models will be handled in methods


logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Service class for analytics operations with multi-tenant support.
    
    Handles dashboard metrics, conversion funnel analysis, team performance,
    revenue analytics, and custom report generation.
    """
    
    def __init__(self, db: Session):
        """Initialize analytics service with database session."""
        self.db = db
    
    async def get_dashboard_overview(
        self, 
        tenant_id: str, 
        date_from: datetime, 
        date_to: datetime
    ) -> dict:
        """
        Get dashboard overview with core KPIs and trends.
        
        Args:
            tenant_id: Tenant identifier for multi-tenant filtering
            date_from: Start date for metrics calculation
            date_to: End date for metrics calculation
            
        Returns:
            Dict matching DashboardOverviewResponse schema
        """
        try:
            logger.info(f"Getting dashboard overview for tenant {tenant_id} from {date_from} to {date_to}")
            
            # Calculate previous period for trend comparison
            period_duration = date_to - date_from
            prev_date_from = date_from - period_duration
            prev_date_to = date_from
            
            # Query current period metrics
            current_metrics = await self._get_period_metrics(tenant_id, date_from, date_to)
            previous_metrics = await self._get_period_metrics(tenant_id, prev_date_from, prev_date_to)
            
            # Calculate trends (percentage change from previous period)
            trends = self._calculate_trends(current_metrics, previous_metrics)
            
            # Get top courses by enrollment count
            top_courses = await self._get_top_courses(tenant_id, date_from, date_to)
            
            # Get recent activities (mock data for now)
            recent_activities = await self._get_recent_activities(tenant_id, date_from, date_to)
            
            return {
                "metrics": {
                    "total_leads": current_metrics["total_leads"],
                    "active_leads": current_metrics["active_leads"], 
                    "converted_leads": current_metrics["converted_leads"],
                    "total_calls": current_metrics["total_calls"],
                    "total_demos": current_metrics["total_demos"],
                    "total_enrollments": current_metrics["total_enrollments"],
                    "revenue": current_metrics["revenue"],
                    "conversion_rate": current_metrics["conversion_rate"],
                    "demo_attendance_rate": current_metrics["demo_attendance_rate"],
                    "call_answer_rate": current_metrics["call_answer_rate"],
                    "period_start": date_from,
                    "period_end": date_to
                },
                "trends": trends,
                "top_courses": top_courses,
                "recent_activities": recent_activities
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_dashboard_overview: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Error in get_dashboard_overview: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def get_conversion_funnel(
        self, 
        tenant_id: str, 
        date_from: datetime, 
        date_to: datetime
    ) -> dict:
        """
        Get conversion funnel analysis with stage-by-stage metrics.
        
        Args:
            tenant_id: Tenant identifier
            date_from: Start date for analysis
            date_to: End date for analysis
            
        Returns:
            Dict matching ConversionFunnelResponse schema
        """
        try:
            logger.info(f"Getting conversion funnel for tenant {tenant_id}")
            
            # Query leads in date range
            total_leads = self.db.query(func.count(Lead.id)).filter(
                and_(
                    Lead.tenant_id == tenant_id,
                    Lead.created_at >= date_from,
                    Lead.created_at <= date_to
                )
            ).scalar() or 0
            
            # Query contacted leads (leads with at least one call)
            contacted_leads = self.db.query(func.count(func.distinct(Call.lead_id))).join(
                Lead, Call.lead_id == Lead.id
            ).filter(
                and_(
                    Lead.tenant_id == tenant_id,
                    Lead.created_at >= date_from,
                    Lead.created_at <= date_to
                )
            ).scalar() or 0
            
            # Query actual demos that were attended/completed
            demo_attended = self.db.query(func.count(func.distinct(Demo.lead_id))).join(
                Lead, Demo.lead_id == Lead.id
            ).filter(
                and_(
                    Demo.tenant_id == tenant_id,
                    Lead.created_at >= date_from,
                    Lead.created_at <= date_to,
                    or_(
                        Demo.attended == True,
                        Demo.completed == True,
                        Demo.outcome == 'completed'
                    )
                )
            ).scalar() or 0
            
            # Query enrolled leads  
            enrolled_leads = self.db.query(func.count(func.distinct(Enrollment.lead_id))).join(
                Lead, Enrollment.lead_id == Lead.id
            ).filter(
                and_(
                    Lead.tenant_id == tenant_id,
                    Lead.created_at >= date_from,
                    Lead.created_at <= date_to,
                    Enrollment.enrolled_at >= date_from,
                    Enrollment.enrolled_at <= date_to
                )
            ).scalar() or 0
            
            # Calculate conversion and drop-off rates
            stages = []
            
            # Lead stage
            stages.append({
                "stage": "Lead",
                "count": total_leads,
                "conversion_rate": 100.0,
                "drop_off_rate": 0.0
            })
            
            # Contacted stage
            contacted_conversion = min(round((contacted_leads / total_leads * 100), 2), 100.0) if total_leads > 0 else 0.0
            contacted_dropoff = max(min(round(100.0 - contacted_conversion, 2), 100.0), 0.0)
            stages.append({
                "stage": "Contacted",
                "count": contacted_leads,
                "conversion_rate": contacted_conversion,
                "drop_off_rate": contacted_dropoff
            })
            
            # Demo Attended stage
            demo_conversion = min(round((demo_attended / contacted_leads * 100), 2), 100.0) if contacted_leads > 0 else 0.0
            demo_dropoff = max(min(round(100.0 - demo_conversion, 2), 100.0), 0.0)
            stages.append({
                "stage": "Demo Attended",
                "count": demo_attended,
                "conversion_rate": demo_conversion,
                "drop_off_rate": demo_dropoff
            })
            
            # Enrolled stage
            enrollment_conversion = min(round((enrolled_leads / demo_attended * 100), 2), 100.0) if demo_attended > 0 else 0.0
            enrollment_dropoff = max(min(round(100.0 - enrollment_conversion, 2), 100.0), 0.0)
            stages.append({
                "stage": "Enrolled",
                "count": enrolled_leads,
                "conversion_rate": enrollment_conversion,
                "drop_off_rate": enrollment_dropoff
            })
            
            # Find bottleneck stage (highest drop-off rate)
            bottleneck_stage = max(stages[1:], key=lambda x: x["drop_off_rate"])["stage"]
            
            # Overall conversion rate
            overall_conversion = min(round((enrolled_leads / total_leads * 100), 2), 100.0) if total_leads > 0 else 0.0
            
            return {
                "stages": stages,
                "overall_conversion_rate": overall_conversion,
                "bottleneck_stage": bottleneck_stage,
                "total_leads": total_leads,
                "total_enrollments": enrolled_leads,
                "date_range": {
                    "start": date_from,
                    "end": date_to
                }
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_conversion_funnel: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Error in get_conversion_funnel: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def get_team_performance(
        self, 
        tenant_id: str, 
        date_from: datetime, 
        date_to: datetime
    ) -> dict:
        """
        Get team performance metrics including individual agent performance.
        
        Args:
            tenant_id: Tenant identifier
            date_from: Start date for analysis
            date_to: End date for analysis
            
        Returns:
            Dict matching TeamPerformanceResponse schema
        """
        try:
            logger.info(f"Getting team performance for tenant {tenant_id}")
            
            # Query agent performance data (direct tenant_id and agent_id on CallLog)
            agent_stats = self.db.query(
                Call.agent_id,
                func.count(Call.id).label('calls_made'),
                func.avg(Call.duration).label('avg_call_duration'),
                func.count(func.distinct(Call.lead_id)).label('unique_leads_contacted')
            ).filter(
                and_(
                    Call.tenant_id == tenant_id,
                    Call.created_at >= date_from,
                    Call.created_at <= date_to,
                    Call.agent_id.isnot(None)
                )
            ).group_by(Call.agent_id).all()
            
            # Get enrollment data per agent (join through Lead since Enrollment has no agent_id)
            try:
                enrollment_stats = self.db.query(
                    Lead.assigned_to.label('agent_id'),
                    func.count(Enrollment.id).label('enrollments_generated')
                ).join(
                    Lead, Enrollment.lead_id == Lead.id
                ).filter(
                    and_(
                        Lead.tenant_id == tenant_id,
                        Enrollment.enrolled_at >= date_from,
                        Enrollment.enrolled_at <= date_to
                    )
                ).group_by(Lead.assigned_to).all()
            except Exception as e:
                logger.warning(f"Could not query enrollment stats per agent: {e}")
                enrollment_stats = []
            
            # Convert to dictionaries for easier lookup
            enrollment_dict = {stat.agent_id: stat.enrollments_generated for stat in enrollment_stats}
            
            # Build agent performance list
            agents = []
            total_team_enrollments = 0
            conversion_rates = []
            
            for stat in agent_stats:
                agent_id = stat.agent_id
                calls_made = stat.calls_made
                avg_call_duration = round(stat.avg_call_duration, 2) if stat.avg_call_duration else 0.0
                enrollments = enrollment_dict.get(agent_id, 0)
                
                # Calculate conversion rate
                conversion_rate = round((enrollments / calls_made * 100), 2) if calls_made > 0 else 0.0
                conversion_rates.append(conversion_rate)
                total_team_enrollments += enrollments
                
                # Mock agent name and satisfaction score
                agent_name = f"Agent {str(agent_id)[-4:]}"
                satisfaction_score = min(round(7.5 + (conversion_rate / 100) * 2.5, 1), 10.0)  # Mock score based on performance
                
                # Query actual demos conducted by this agent (as mentor)
                try:
                    demos_conducted = self.db.query(func.count(Demo.id)).filter(
                        and_(
                            Demo.tenant_id == tenant_id,
                            Demo.mentor_id == agent_id,
                            Demo.created_at >= date_from,
                            Demo.created_at <= date_to
                        )
                    ).scalar() or 0
                except Exception:
                    demos_conducted = 0
                
                agents.append({
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "calls_made": calls_made,
                    "demos_conducted": demos_conducted,
                    "enrollments_generated": enrollments,
                    "conversion_rate": conversion_rate,
                    "avg_call_duration": avg_call_duration,
                    "satisfaction_score": satisfaction_score
                })
            
            # Calculate team averages
            team_avg_conversion = round(sum(conversion_rates) / len(conversion_rates), 2) if conversion_rates else 0.0
            
            # Find top performer (highest conversion rate)
            top_performer = max(agents, key=lambda x: x["conversion_rate"])["agent_id"] if agents else None
            
            return {
                "agents": agents,
                "team_avg_conversion": team_avg_conversion,
                "top_performer": top_performer,
                "total_team_enrollments": total_team_enrollments
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_team_performance: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Error in get_team_performance: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def get_revenue_analytics(
        self, 
        tenant_id: str, 
        date_from: datetime, 
        date_to: datetime
    ) -> dict:
        """
        Get revenue analytics including total revenue, course breakdown, and forecasting.
        
        Args:
            tenant_id: Tenant identifier
            date_from: Start date for analysis
            date_to: End date for analysis
            
        Returns:
            Dict matching RevenueAnalyticsResponse schema
        """
        try:
            logger.info(f"Getting revenue analytics for tenant {tenant_id}")
            
            # Query total revenue
            total_revenue = self.db.query(func.sum(Enrollment.total_amount)).filter(
                and_(
                    Enrollment.tenant_id == tenant_id,
                    Enrollment.enrolled_at >= date_from,
                    Enrollment.enrolled_at <= date_to
                )
            ).scalar() or 0.0
            
            # Query revenue by course
            course_revenue = self.db.query(
                Enrollment.course_id,
                func.sum(Enrollment.total_amount).label('total_revenue'),
                func.count(Enrollment.id).label('enrollment_count')
            ).filter(
                and_(
                    Enrollment.tenant_id == tenant_id,
                    Enrollment.enrolled_at >= date_from,
                    Enrollment.enrolled_at <= date_to
                )
            ).group_by(Enrollment.course_id).all()
            
            # Build revenue breakdown
            revenue_by_course = []
            for course_stat in course_revenue:
                course_id = course_stat.course_id
                course_revenue_amount = float(course_stat.total_revenue)
                enrollment_count = course_stat.enrollment_count
                avg_revenue_per_student = round(course_revenue_amount / enrollment_count, 2) if enrollment_count > 0 else 0.0
                revenue_share_percent = round((course_revenue_amount / total_revenue * 100), 2) if total_revenue > 0 else 0.0
                
                revenue_by_course.append({
                    "course_id": str(course_id),
                    "course_name": f"Course {str(course_id)[-4:]}",  # Mock course name
                    "total_revenue": course_revenue_amount,
                    "enrollment_count": enrollment_count,
                    "avg_revenue_per_student": avg_revenue_per_student,
                    "revenue_share_percent": revenue_share_percent
                })
            
            # Generate monthly revenue time series
            monthly_revenue = await self._get_monthly_revenue_series(tenant_id, date_from, date_to)
            
            # Calculate growth rate vs previous period
            period_duration = date_to - date_from
            prev_date_from = date_from - period_duration
            prev_date_to = date_from
            
            prev_revenue = self.db.query(func.sum(Enrollment.total_amount)).filter(
                and_(
                    Enrollment.tenant_id == tenant_id,
                    Enrollment.enrolled_at >= prev_date_from,
                    Enrollment.enrolled_at <= prev_date_to
                )
            ).scalar() or 0.0
            
            growth_rate = round(((total_revenue - prev_revenue) / prev_revenue * 100), 2) if prev_revenue > 0 else 0.0
            
            # Simple forecast for next month (trend-based)
            forecast_next_month = total_revenue * (1 + (growth_rate / 100)) if growth_rate > 0 else total_revenue
            
            return {
                "total_revenue": float(total_revenue),
                "revenue_by_course": revenue_by_course,
                "monthly_revenue": monthly_revenue,
                "forecast_next_month": round(forecast_next_month, 2),
                "growth_rate": growth_rate,
                "date_range": {
                    "start": date_from,
                    "end": date_to
                }
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_revenue_analytics: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Error in get_revenue_analytics: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def generate_custom_report(
        self, 
        tenant_id: str, 
        report_type: str, 
        date_from: datetime, 
        date_to: datetime, 
        filters: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        Generate custom report based on type and filters.
        
        Args:
            tenant_id: Tenant identifier
            report_type: Type of report to generate
            date_from: Start date for report
            date_to: End date for report
            filters: Optional filters to apply
            
        Returns:
            Dict matching ReportResponse schema
        """
        try:
            logger.info(f"Generating custom report '{report_type}' for tenant {tenant_id}")
            
            report_id = uuid.uuid4()
            generated_at = datetime.utcnow()
            
            # Route to appropriate analytics method based on report type
            if report_type == "dashboard_overview":
                data = await self.get_dashboard_overview(tenant_id, date_from, date_to)
            elif report_type == "conversion_funnel":
                data = await self.get_conversion_funnel(tenant_id, date_from, date_to)
            elif report_type == "team_performance":
                data = await self.get_team_performance(tenant_id, date_from, date_to)
            elif report_type == "revenue_analytics":
                data = await self.get_revenue_analytics(tenant_id, date_from, date_to)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")
            
            # Apply additional filters if provided
            if filters:
                data = self._apply_report_filters(data, filters)
            
            # Mock export URL
            export_url = f"/api/reports/export/{report_id}"
            
            return {
                "report_id": report_id,
                "report_type": report_type,
                "generated_at": generated_at,
                "data": data,
                "export_url": export_url
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in generate_custom_report: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # Helper Methods
    
    async def _get_period_metrics(self, tenant_id: str, date_from: datetime, date_to: datetime) -> dict:
        """Get metrics for a specific time period."""
        # Query total leads
        total_leads = self.db.query(func.count(Lead.id)).filter(
            and_(
                Lead.tenant_id == tenant_id,
                Lead.created_at >= date_from,
                Lead.created_at <= date_to
            )
        ).scalar() or 0
        
        # Query active leads (exclude enrolled/lost)
        active_leads = self.db.query(func.count(Lead.id)).filter(
            and_(
                Lead.tenant_id == tenant_id,
                Lead.created_at >= date_from,
                Lead.created_at <= date_to,
                Lead.status.in_([
                    LeadStatus.NEW,
                    LeadStatus.CONTACTED,
                    LeadStatus.QUALIFIED,
                    LeadStatus.DEMO_SCHEDULED,
                    LeadStatus.DEMO_COMPLETED,
                    LeadStatus.NURTURING,
                ])
            )
        ).scalar() or 0
        
        # Query converted leads (enrollments)
        converted_leads = self.db.query(func.count(func.distinct(Enrollment.lead_id))).join(
            Lead, Enrollment.lead_id == Lead.id
        ).filter(
            and_(
                Lead.tenant_id == tenant_id,
                Enrollment.enrolled_at >= date_from,
                Enrollment.enrolled_at <= date_to
            )
        ).scalar() or 0
        
        # Query total calls (direct tenant_id filter on CallLog)
        try:
            total_calls = self.db.query(func.count(Call.id)).filter(
                and_(
                    Call.tenant_id == tenant_id,
                    Call.created_at >= date_from,
                    Call.created_at <= date_to
                )
            ).scalar() or 0
        except Exception as e:
            logger.warning(f"Could not query call logs: {e}")
            total_calls = 0
        
        # Query actual demo count
        try:
            total_demos = self.db.query(func.count(Demo.id)).filter(
                and_(
                    Demo.tenant_id == tenant_id,
                    Demo.scheduled_at >= date_from,
                    Demo.scheduled_at <= date_to
                )
            ).scalar() or 0
        except Exception as demo_err:
            logger.warning(f"Could not query demos: {demo_err}")
            total_demos = 0

        # Query attended/completed demos for attendance rate
        try:
            attended_demos = self.db.query(func.count(Demo.id)).filter(
                and_(
                    Demo.tenant_id == tenant_id,
                    Demo.scheduled_at >= date_from,
                    Demo.scheduled_at <= date_to,
                    or_(
                        Demo.attended == True,
                        Demo.completed == True,
                        Demo.outcome == 'completed'
                    )
                )
            ).scalar() or 0
        except Exception as attend_err:
            logger.warning(f"Could not query attended demos: {attend_err}")
            attended_demos = 0

        # Query total enrollments
        total_enrollments = converted_leads
        
        # Query revenue
        revenue = self.db.query(func.sum(Enrollment.total_amount)).filter(
            and_(
                Enrollment.tenant_id == tenant_id,
                Enrollment.enrolled_at >= date_from,
                Enrollment.enrolled_at <= date_to
            )
        ).scalar() or 0.0
        
        # Calculate rates
        conversion_rate = round((converted_leads / total_leads * 100), 2) if total_leads > 0 else 0.0
        # demo_attendance_rate: attended demos out of total scheduled demos, capped at 100
        demo_attendance_rate = round((attended_demos / total_demos * 100), 2) if total_demos > 0 else 0.0
        
        # Mock call answer rate (75% average)
        call_answer_rate = 75.0
        
        return {
            "total_leads": total_leads,
            "active_leads": active_leads,
            "converted_leads": converted_leads,
            "total_calls": total_calls,
            "total_demos": total_demos,
            "total_enrollments": total_enrollments,
            "revenue": float(revenue),
            "conversion_rate": conversion_rate,
            "demo_attendance_rate": demo_attendance_rate,
            "call_answer_rate": call_answer_rate
        }
    
    def _calculate_trends(self, current: dict, previous: dict) -> dict:
        """Calculate percentage trends between current and previous periods."""
        trends = {}
        
        for key in ["total_leads", "converted_leads", "revenue", "conversion_rate"]:
            current_val = current.get(key, 0)
            previous_val = previous.get(key, 0)
            
            if previous_val > 0:
                trend = round(((current_val - previous_val) / previous_val * 100), 2)
            else:
                trend = 100.0 if current_val > 0 else 0.0
            
            trends[key] = trend
        
        return trends
    
    async def _get_top_courses(self, tenant_id: str, date_from: datetime, date_to: datetime) -> List[dict]:
        """Get top courses by enrollment count."""
        course_stats = self.db.query(
            Enrollment.course_id,
            func.count(Enrollment.id).label('enrollment_count'),
            func.sum(Enrollment.total_amount).label('revenue')
        ).filter(
            and_(
                Enrollment.tenant_id == tenant_id,
                Enrollment.enrolled_at >= date_from,
                Enrollment.enrolled_at <= date_to
            )
        ).group_by(Enrollment.course_id).order_by(func.count(Enrollment.id).desc()).limit(5).all()
        
        top_courses = []
        for stat in course_stats:
            top_courses.append({
                "course_id": str(stat.course_id),
                "course_name": f"Course {str(stat.course_id)[-4:]}",
                "enrollment_count": stat.enrollment_count,
                "revenue": float(stat.revenue or 0)
            })
        
        return top_courses
    
    async def _get_recent_activities(self, tenant_id: str, date_from: datetime, date_to: datetime) -> List[dict]:
        """Get recent activities (mock data for now)."""
        return [
            {
                "activity": "New enrollment in Python Basics",
                "timestamp": datetime.utcnow() - timedelta(hours=2),
                "type": "enrollment"
            },
            {
                "activity": "Demo scheduled for Data Science course",
                "timestamp": datetime.utcnow() - timedelta(hours=4),
                "type": "demo"
            },
            {
                "activity": "New lead from website",
                "timestamp": datetime.utcnow() - timedelta(hours=6),
                "type": "lead"
            }
        ]
    
    async def _get_monthly_revenue_series(self, tenant_id: str, date_from: datetime, date_to: datetime) -> List[dict]:
        """Get monthly revenue time series data."""
        # Mock monthly revenue data for now
        monthly_data = []
        current_date = date_from.replace(day=1)  # Start of month
        
        while current_date <= date_to:
            # Mock revenue calculation
            month_revenue = 15000 + (current_date.month * 1000)  # Mock increasing trend
            
            monthly_data.append({
                "date": current_date,
                "value": float(month_revenue),
                "metric": "revenue"
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return monthly_data
    
    def _apply_report_filters(self, data: dict, filters: dict) -> dict:
        """Apply additional filters to report data."""
        # Simple filter implementation - can be extended based on requirements
        filtered_data = data.copy()
        
        # Example filters
        if "min_revenue" in filters:
            # Filter revenue data if applicable
            pass
        
        if "agent_ids" in filters:
            # Filter agent data if applicable
            if "agents" in filtered_data:
                agent_ids = filters["agent_ids"]
                filtered_data["agents"] = [
                    agent for agent in filtered_data["agents"] 
                    if agent["agent_id"] in agent_ids
                ]
        
        return filtered_data