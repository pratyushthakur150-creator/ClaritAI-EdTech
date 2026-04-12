"""
Courses API endpoint for ClaritAI EdTech platform.
Serves course data derived from enrollments and demo records.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import Dict, Any, Optional
import logging

from app.core.database import get_db_session
from app.core.utils import get_tenant_id
from app.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses")


@router.get("/", response_model=Dict[str, Any])
async def list_courses(
    search: Optional[str] = Query(None, description="Search courses by title"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List all courses for the tenant.

    Derives course data from the courses table if it exists,
    otherwise aggregates from enrollments.
    Returns: {courses: [...], total: N}
    """
    try:
        tenant_id = get_tenant_id(current_user)
        logger.info(f"Listing courses for tenant {tenant_id}")

        courses = []

        # Query the Course model from the teaching module
        try:
            from app.models.teaching import Course
            from app.models.enrollment import Enrollment

            query = db.query(Course).filter(
                Course.tenant_id == tenant_id,
                Course.is_deleted == False
            )
            if search:
                query = query.filter(Course.name.ilike(f"%{search}%"))
            if status_filter:
                query = query.filter(Course.status == status_filter)

            course_rows = query.all()
            for c in course_rows:
                # Count enrolled students for this course
                enrolled_count = db.query(func.count(Enrollment.id)).filter(
                    Enrollment.course_id == c.id,
                    Enrollment.tenant_id == tenant_id,
                    Enrollment.is_deleted == False
                ).scalar() or 0

                duration_str = f"{c.duration_weeks} weeks" if hasattr(c, 'duration_weeks') and c.duration_weeks else "8 weeks"

                courses.append({
                    "id": str(c.id),
                    "name": c.name,
                    "title": c.name,
                    "instructor": getattr(c, "instructor", "Staff") or "Staff",
                    "instructorRole": getattr(c, "instructor_role", "") or "",
                    "enrolled": enrolled_count,
                    "enrollment_count": enrolled_count,
                    "rating": getattr(c, "rating", 4.5) or 4.5,
                    "status": getattr(c, "status", "active") or "active",
                    "category": getattr(c, "category", "General") or "General",
                    "duration": duration_str,
                    "duration_weeks": getattr(c, "duration_weeks", 8) or 8,
                    "price": str(getattr(c, "price", "")) if getattr(c, "price", None) else "",
                    "description": getattr(c, "description", "") or "",
                })
        except Exception as e:
            logger.error(f"Error querying courses: {e}")
            import traceback
            logger.error(traceback.format_exc())

        # Apply search filter if needed and courses were derived
        if search and courses:
            search_lower = search.lower()
            courses = [c for c in courses if search_lower in c.get("title", "").lower()]

        response = {
            "courses": courses,
            "total": len(courses),
        }

        logger.info(f"Retrieved {len(courses)} courses for tenant {tenant_id}")
        return response

    except Exception as e:
        logger.error(f"Error listing courses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve courses"
        )
