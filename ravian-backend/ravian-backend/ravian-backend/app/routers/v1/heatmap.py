"""
Heatmap Router for Teaching Assistant Module

This module provides FastAPI endpoints for retrieving course confusion heatmap data.
The heatmap shows module-level confusion scores based on student interactions and 
confidence levels, helping instructors identify areas where students struggle most.

Endpoints:
- GET /heatmap/course/{course_id}: Get confusion heatmap for a specific course
- GET /heatmap/health: Health check endpoint

Authentication: All endpoints except health check require valid JWT authentication
Multi-tenancy: All data is filtered by tenant_id from authenticated user
"""

import logging
from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services.heatmap_service import HeatmapService
from app.schemas.heatmap import HeatmapResponse
from app.core.database import get_db_session
from app.dependencies.auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(
    prefix="/heatmap",
    responses={
        404: {"description": "Course not found"},
        403: {"description": "Access forbidden - insufficient permissions"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)


@router.get(
    "/course/{course_id}",
    response_model=HeatmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Course Confusion Heatmap",
    description="Retrieve confusion heatmap data for a specific course showing module-level confusion scores"
)
async def get_course_confusion_heatmap(
    course_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> HeatmapResponse:
    """
    Retrieve confusion heatmap data for a specific course.
    
    This endpoint analyzes student interactions within a course to generate a heatmap
    showing confusion levels across different modules. The confusion score is calculated
    based on the confidence levels of student interactions, with lower confidence
    indicating higher confusion.
    
    Parameters:
    - course_id: UUID of the course to analyze
    
    Authentication:
    - Requires valid JWT token
    - Data is filtered by tenant_id from authenticated user
    
    Response Structure:
    
        {
            "course_id": "uuid-string",
            "heatmap_data": {
                "module_id_1": {
                    "confusion_score": 75.5,
                    "interaction_count": 25,
                    "top_confused_topics": ["Topic A", "Topic B"]
                }
            },
            "overall_metrics": {
                "most_confused_module": "module_id_1",
                "least_confused_module": "module_id_2", 
                "average_confusion_score": 65.2,
                "total_interactions": 150
            }
        }
    
    Usage Examples:
    
    Python:
    
        # Using requests
        import requests
        
        headers = {"Authorization": f"Bearer {jwt_token}"}
        response = requests.get(
            f"https://api.example.com/heatmap/course/{course_id}",
            headers=headers
        )
        heatmap_data = response.json()
    
    JavaScript:
    
        // Using fetch
        const response = await fetch(`/heatmap/course/${courseId}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        const heatmapData = await response.json();
    
    Error Handling:
    - 401 Unauthorized: Invalid or missing JWT token
    - 403 Forbidden: User doesn't have access to this course's data
    - 404 Not Found: Course doesn't exist or no data available
    - 422 Validation Error: Invalid course_id format
    - 500 Internal Server Error: Database connection issues or unexpected errors
    
    Business Logic:
    1. Extract tenant_id from authenticated user's JWT token
    2. Create HeatmapService instance with database session
    3. Query course modules and student interactions for the specified course
    4. Calculate confusion scores: (1 - average_confidence) * 100
    5. Identify top confused topics per module
    6. Generate overall course metrics
    7. Return structured heatmap response
    
    Performance Considerations:
    - Uses optimized SQLAlchemy queries with proper indexing
    - Multi-tenant filtering ensures data isolation
    - Caching recommended for frequently accessed courses
    """
    
    try:
        logger.info(f"Fetching heatmap data for course_id: {course_id}")
        # Extract tenant_id from current user JWT
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            logger.error("No tenant_id found in current_user JWT")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden - invalid tenant information"
            )
        
        logger.info(f"Processing heatmap request for tenant_id: {tenant_id}, course_id: {course_id}")
        
        # Create HeatmapService instance and get heatmap data
        heatmap_service = HeatmapService(db)
        heatmap_data = heatmap_service.get_course_heatmap(
            course_id=course_id,
            tenant_id=UUID(tenant_id)
        )
        
        logger.info(f"Successfully retrieved heatmap data for course {course_id}")
        logger.debug(f"Heatmap data summary: {len(heatmap_data.get('heatmap_data', {}))} modules analyzed")
        
        return HeatmapResponse(**heatmap_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions (from service layer)
        raise
    except ValueError as e:
        logger.error(f"Invalid UUID format for course_id {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid course_id format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving heatmap for course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing heatmap request"
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check the health status of the heatmap service",
    tags=["Health"]
)
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for the heatmap service.
    
    This endpoint provides a simple health check to verify that the heatmap
    service is running and accessible. It doesn't require authentication.
    
    Returns:
    
        {
            "status": "healthy",
            "service": "heatmap",
            "version": "1.0.0"
        }
    """
    logger.info("Heatmap service health check requested")
    return {
        "status": "healthy",
        "service": "heatmap",
        "version": "1.0.0"
    }
