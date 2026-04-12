"""
Teaching router — Course management endpoints.
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db_session
from app.core.utils import get_tenant_id
from app.dependencies.auth import get_current_user
from app.models.teaching import Course

router = APIRouter()
logger = logging.getLogger(__name__)



@router.get("/courses", response_model=Dict[str, Any])
async def list_courses(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List all courses for the current tenant with pagination and filtering.
    """
    try:
        tenant_id = get_tenant_id(current_user)
        logger.info(f"Listing courses for tenant {tenant_id}, page {page}")

        query = db.query(Course).filter(
            Course.tenant_id == tenant_id,
            Course.is_deleted == False
        )

        if category:
            query = query.filter(Course.category == category)

        if search:
            query = query.filter(Course.name.ilike(f"%{search}%"))

        total = query.count()
        courses = query.order_by(Course.created_at.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        total_pages = (total + per_page - 1) // per_page

        from app.models.enrollment import Enrollment
        from sqlalchemy import func

        course_list = []
        for c in courses:
            # Dynamically count enrollments for this course
            dynamic_student_count = db.query(func.count(Enrollment.id)).filter(
                Enrollment.course_id == c.id,
                Enrollment.tenant_id == tenant_id
            ).scalar()

            course_list.append({
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "course_code": c.course_code,
                "category": c.category,
                "difficulty_level": c.difficulty_level,
                "duration_weeks": c.duration_weeks,
                "total_hours": c.total_hours,
                "price": c.price,
                "currency": c.currency,
                "max_students": c.max_students,
                "enrollment_count": dynamic_student_count or 0,
                "completion_rate": c.completion_rate or 0,
                "average_rating": c.average_rating or 0,
                "is_active": c.is_active,
                "is_published": c.is_published,
                "student_count": dynamic_student_count or 0,
                "status": "active" if c.is_active == "true" else "draft",
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            })

        return {
            "data": course_list,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }

    except Exception as e:
        logger.error(f"Error listing courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list courses"
        )


@router.get("/courses/{course_id}", response_model=Dict[str, Any])
async def get_course(
    course_id: UUID,
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a single course by ID.
    """
    try:
        tenant_id = get_tenant_id(current_user)
        course = db.query(Course).filter(
            Course.id == course_id,
            Course.tenant_id == tenant_id,
            Course.is_deleted == False
        ).first()

        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )

        from app.models.enrollment import Enrollment
        from sqlalchemy import func
        dynamic_student_count = db.query(func.count(Enrollment.id)).filter(
            Enrollment.course_id == course.id,
            Enrollment.tenant_id == tenant_id
        ).scalar() or 0

        return {
            "id": str(course.id),
            "name": course.name,
            "description": course.description,
            "course_code": course.course_code,
            "category": course.category,
            "difficulty_level": course.difficulty_level,
            "duration_weeks": course.duration_weeks,
            "total_hours": course.total_hours,
            "price": course.price,
            "currency": course.currency,
            "max_students": course.max_students,
            "enrollment_count": dynamic_student_count,
            "student_count": dynamic_student_count,
            "syllabus": course.syllabus,
            "modules": course.modules,
            "prerequisites": course.prerequisites,
            "learning_outcomes": course.learning_outcomes,
            "is_active": course.is_active,
            "is_published": course.is_published,
            "created_at": course.created_at.isoformat() if course.created_at else None,
            "updated_at": course.updated_at.isoformat() if course.updated_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch course"
        )


@router.post("/courses", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: Dict[str, Any],
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new course.
    """
    try:
        tenant_id = get_tenant_id(current_user)
        logger.info(f"Creating course for tenant {tenant_id}")

        course = Course(
            tenant_id=tenant_id,
            name=course_data.get("name", ""),
            description=course_data.get("description"),
            course_code=course_data.get("course_code"),
            category=course_data.get("category"),
            difficulty_level=course_data.get("difficulty_level"),
            duration_weeks=course_data.get("duration_weeks"),
            total_hours=course_data.get("total_hours"),
            price=course_data.get("price"),
            currency=course_data.get("currency", "USD"),
            max_students=course_data.get("max_students"),
            is_active="true",
            is_published="false",
        )

        db.add(course)
        db.commit()
        db.refresh(course)

        logger.info(f"✓ Course created: {course.id}")
        return {
            "id": str(course.id),
            "name": course.name,
            "description": course.description,
            "status": "active",
            "created_at": course.created_at.isoformat() if course.created_at else None,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create course"
        )


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: UUID,
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Soft-delete a course (sets is_deleted=True)."""
    try:
        tenant_id = get_tenant_id(current_user)
        course = db.query(Course).filter(
            Course.id == course_id,
            Course.tenant_id == tenant_id
        ).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        course.is_deleted = True
        db.commit()
        logger.info(f"Course {course_id} soft-deleted for tenant {tenant_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete course"
        )
