"""
Students API endpoint.
Returns student list for the frontend Students page.
Queries the Student model with real enrollment/course data.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

from app.core.database import get_db_session
from app.dependencies.auth import get_optional_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/students")


def _time_ago(dt, now):
    """Convert a datetime to '2h ago' style string."""
    if not dt:
        return "N/A"
    try:
        # Make both timezone-aware or both naive
        if dt.tzinfo is not None and now.tzinfo is None:
            dt = dt.replace(tzinfo=None)
        elif dt.tzinfo is None and now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        diff = now - dt
        secs = int(diff.total_seconds())
        if secs < 0:
            return "Just now"
        if secs < 60:
            return "Just now"
        if secs < 3600:
            return f"{secs // 60}m ago"
        if secs < 86400:
            return f"{secs // 3600}h ago"
        days = secs // 86400
        if days == 1:
            return "Yesterday"
        if days < 7:
            return f"{days}d ago"
        if days < 30:
            return f"{days // 7}w ago"
        return dt.strftime("%d %b %Y")
    except Exception:
        return "N/A"


@router.get("")
async def list_students(
    search: Optional[str] = Query(None, description="Search by name"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
):
    """
    Return enrolled students with real data from Student model.
    Joins Student → Enrollment → Course and Lead for names/emails.
    """
    tenant_id = current_user.get("tenant_id")
    logger.info(f"Student list requested for tenant {tenant_id}")

    students = []
    total = 0
    now = datetime.now()

    try:
        from app.models.enrollment import Student, Enrollment
        from app.models.lead import Lead
        from app.models.teaching import Course

        # Query Student model with joins
        query = (
            db.query(Student, Lead.name, Lead.email, Course.name.label("course_name"))
            .join(Enrollment, Student.enrollment_id == Enrollment.id)
            .join(Lead, Student.lead_id == Lead.id)
            .outerjoin(Course, Enrollment.course_id == Course.id)
            .filter(Student.tenant_id == tenant_id)
        )

        if search:
            query = query.filter(Lead.name.ilike(f"%{search}%"))

        total = query.count()
        rows = query.offset((page - 1) * limit).limit(limit).all()

        for student, lead_name, lead_email, course_name in rows:
            risk = "low"
            if hasattr(student, "risk_level") and student.risk_level:
                risk = student.risk_level.value if hasattr(student.risk_level, "value") else str(student.risk_level)

            students.append({
                "id": str(student.id),
                "name": lead_name or "Unknown",
                "email": lead_email or "",
                "course": course_name or "General",
                "progress": float(student.completion_percentage or 0),
                "attendance": float(student.engagement_score or 0),
                "risk": risk,
                "risk_score": student.risk_score or 0,
                "lastActive": _time_ago(student.last_active, now),
                "engagement_score": student.engagement_score or 0,
                "modules_completed": student.modules_completed or 0,
                "modules_total": student.modules_total or 0,
                "assignments_completed": student.assignments_completed or 0,
                "assignments_total": student.assignments_total or 0,
                "study_hours": float(student.total_study_hours or 0),
                "current_module": student.current_module or "",
                "login_streak": student.login_streak or 0,
            })

        if students:
            # Compute summary stats
            avg_progress = round(sum(s["progress"] for s in students) / len(students), 1) if students else 0
            at_risk = len([s for s in students if s["risk"] in ("high", "critical")])
            avg_engagement = round(sum(s["engagement_score"] for s in students) / len(students), 1) if students else 0

            return {
                "students": students,
                "total": total,
                "summary": {
                    "avg_progress": avg_progress,
                    "at_risk_count": at_risk,
                    "avg_engagement": avg_engagement,
                },
            }
    except Exception as e:
        logger.error(f"Error querying students: {e}", exc_info=True)

    # If no Student records, try Enrollment + Lead fallback
    try:
        from app.models.enrollment import Enrollment
        from app.models.lead import Lead
        from app.models.teaching import Course

        query = (
            db.query(Lead.id, Lead.name, Lead.email, Course.name.label("course_name"),
                     Enrollment.enrolled_at, Enrollment.total_amount)
            .join(Enrollment, Enrollment.lead_id == Lead.id)
            .outerjoin(Course, Enrollment.course_id == Course.id)
            .filter(Lead.tenant_id == tenant_id, Lead.is_deleted == False)
        )
        if search:
            query = query.filter(Lead.name.ilike(f"%{search}%"))
        total = query.count()
        rows = query.offset((page - 1) * limit).limit(limit).all()

        for lead_id, name, email, course_name, enrolled_at, amount in rows:
            students.append({
                "id": str(lead_id),
                "name": name or "Unknown",
                "email": email or "",
                "course": course_name or "General",
                "progress": 0,
                "attendance": 0,
                "risk": "low",
                "risk_score": 0,
                "lastActive": _time_ago(enrolled_at, now),
                "engagement_score": 0,
                "modules_completed": 0,
                "modules_total": 0,
                "assignments_completed": 0,
                "assignments_total": 0,
                "study_hours": 0,
                "current_module": "",
                "login_streak": 0,
            })

        return {"students": students, "total": total, "summary": {"avg_progress": 0, "at_risk_count": 0, "avg_engagement": 0}}
    except Exception as e:
        logger.error(f"Fallback student query error: {e}", exc_info=True)

    return {"students": [], "total": 0, "summary": {"avg_progress": 0, "at_risk_count": 0, "avg_engagement": 0}}
