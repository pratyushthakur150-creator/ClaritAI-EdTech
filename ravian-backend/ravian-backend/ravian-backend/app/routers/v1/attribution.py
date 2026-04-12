"""
Attribution API router for AI EdTech CRM platform.
Handles funnel metrics, source attribution, and speed-to-lead analysis endpoints.
"""

import logging
from datetime import datetime, date, timedelta, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

# FIX: Correct imports matching your project structure
from app.core.database import get_db_session
from app.core.utils import get_tenant_id
from app.dependencies.auth import get_current_user
from app.services.attribution_service import AttributionService
from app.schemas.attribution import (
    FunnelMetrics,
    SourceAttribution,
    SpeedToLeadAnalysis,
    AttributionDateRange
)

# Set up logging
logger = logging.getLogger(__name__)

# FIX: Removed prefix from router definition - prefix is set in __init__.py
router = APIRouter()


def validate_date_range(start_date: Optional[date], end_date: Optional[date]) -> tuple:
    """
    Validate and normalize date range parameters.
    Returns tuple of (start_date, end_date) with defaults applied.
    Raises HTTPException for invalid ranges.
    """
    # Apply defaults: last 30 days if no dates provided
    if not start_date and not end_date:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
    elif not start_date and end_date:
        start_date = end_date - timedelta(days=30)
    elif start_date and not end_date:
        end_date = date.today()

    # Validate date range
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_DATE_RANGE",
                "message": "Start date must be before or equal to end date",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )

    # Check maximum range (2 years)
    days_diff = (end_date - start_date).days
    if days_diff > 730:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "DATE_RANGE_TOO_LARGE",
                "message": "Date range cannot exceed 2 years",
                "days_requested": days_diff,
                "max_days": 730
            }
        )

    return start_date, end_date


@router.get("/funnel", response_model=FunnelMetrics)
async def get_funnel_metrics(
    start_date: Optional[date] = Query(
        None,
        description="Start date for funnel analysis (ISO format: YYYY-MM-DD). Defaults to 30 days ago."
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for funnel analysis (ISO format: YYYY-MM-DD). Defaults to today."
    ),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get funnel conversion metrics from visitors to enrollments.
    """
    try:
        # Extract tenant_id using utility function
        tenant_id = get_tenant_id(current_user)
        validated_start, validated_end = validate_date_range(start_date, end_date)

        # FIX: Convert date to datetime for service layer
        from datetime import datetime
        start_dt = datetime.combine(validated_start, datetime.min.time())
        end_dt = datetime.combine(validated_end, datetime.max.time())

        logger.info(f"Fetching funnel metrics for tenant {tenant_id} from {validated_start} to {validated_end}")

        attribution_service = AttributionService(db)
        funnel_metrics = attribution_service.get_funnel_metrics(
            tenant_id=tenant_id,
            date_range=(start_dt, end_dt)
        )

        return funnel_metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch funnel metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "FUNNEL_METRICS_FAILED", "message": "Failed to retrieve funnel metrics"}
        )


@router.get("/by-source", response_model=List[SourceAttribution])
async def get_source_attribution(
    start_date: Optional[date] = Query(
        None,
        description="Start date for source attribution analysis (ISO format: YYYY-MM-DD). Defaults to 30 days ago."
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for source attribution analysis (ISO format: YYYY-MM-DD). Defaults to today."
    ),
    sources: Optional[str] = Query(
        None,
        description="Comma-separated list of sources to filter (chatbot,organic,paid,referral,direct,social,email)."
    ),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get conversion rates and performance metrics by lead source.
    """
    try:
        # Extract tenant_id using utility function
        tenant_id = get_tenant_id(current_user)
        validated_start, validated_end = validate_date_range(start_date, end_date)

        from datetime import datetime
        start_dt = datetime.combine(validated_start, datetime.min.time())
        end_dt = datetime.combine(validated_end, datetime.max.time())

        # Parse and validate sources filter
        source_filter = None
        if sources:
            source_list = [s.strip().lower() for s in sources.split(",")]
            valid_sources = {"chatbot", "organic", "paid", "referral", "direct", "social", "email"}
            invalid_sources = set(source_list) - valid_sources
            if invalid_sources:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "INVALID_SOURCES",
                        "message": f"Invalid sources: {invalid_sources}",
                        "valid_sources": list(valid_sources)
                    }
                )
            source_filter = source_list

        logger.info(f"Fetching source attribution for tenant {tenant_id}")

        attribution_service = AttributionService(db)
        source_attribution = attribution_service.get_source_attribution(
            tenant_id=tenant_id,
            date_range=(start_dt, end_dt),
            source_filter=source_filter
        )

        return source_attribution

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch source attribution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "SOURCE_ATTRIBUTION_FAILED", "message": "Failed to retrieve source attribution data"}
        )


@router.get("/speed-to-lead", response_model=SpeedToLeadAnalysis)
async def get_speed_to_lead_analysis(
    start_date: Optional[date] = Query(
        None,
        description="Start date for speed-to-lead analysis (ISO format: YYYY-MM-DD). Defaults to 30 days ago."
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for speed-to-lead analysis (ISO format: YYYY-MM-DD). Defaults to today."
    ),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Analyze conversion impact based on lead response time.
    """
    try:
        # Extract tenant_id using utility function
        tenant_id = get_tenant_id(current_user)
        validated_start, validated_end = validate_date_range(start_date, end_date)

        from datetime import datetime
        start_dt = datetime.combine(validated_start, datetime.min.time())
        end_dt = datetime.combine(validated_end, datetime.max.time())

        logger.info(f"Fetching speed-to-lead analysis for tenant {tenant_id}")

        attribution_service = AttributionService(db)
        speed_analysis = attribution_service.get_speed_to_lead_analysis(
            tenant_id=tenant_id,
            date_range=(start_dt, end_dt)
        )

        return speed_analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch speed-to-lead analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "SPEED_TO_LEAD_FAILED", "message": "Failed to retrieve speed-to-lead analysis"}
        )


@router.get("/health")
async def attribution_health():
    """Health check endpoint for attribution analytics module."""
    return {
        "status": "healthy",
        "module": "attribution",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoints": [
            "GET /api/v1/attribution/funnel",
            "GET /api/v1/attribution/by-source",
            "GET /api/v1/attribution/speed-to-lead"
        ]
    }