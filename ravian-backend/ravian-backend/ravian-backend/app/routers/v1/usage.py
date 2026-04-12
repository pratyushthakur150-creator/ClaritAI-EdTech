"""
Usage Router Implementation
File: /app/routers/v1/usage.py
"""

import logging
from datetime import datetime
from typing_extensions import Literal

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies.auth import get_current_user
from app.core.database import get_db_session
from app.core.redis_client import get_redis_client
from app.services.usage import UsageService
from app.schemas.usage import (
    UsageMetrics,
    UsageCheckRequest,
    UsageCheckResponse,
    UsageHistoryResponse,
    PlanLimits
)

logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str
    module: str
    timestamp: datetime


router = APIRouter()


def get_usage_service(
    db: Session = Depends(get_db_session),
    redis_client=Depends(get_redis_client)
) -> UsageService:
    """Dependency to create UsageService instance"""
    return UsageService(db=db, redis_client=redis_client)


@router.get("/current", response_model=UsageMetrics)
async def get_current_usage(
    current_user: dict = Depends(get_current_user),
    usage_service: UsageService = Depends(get_usage_service)
):
    """
    Get current month usage metrics for authenticated tenant

    Returns:
        UsageMetrics: Current usage data including leads, calls, students, credits
    """
    try:
        tenant_id = current_user["tenant_id"]
        logger.info(f"Getting current usage for tenant {tenant_id}")

        usage_metrics = usage_service.get_current_usage(tenant_id=tenant_id)

        logger.info(f"Retrieved current usage for tenant {tenant_id}")
        return usage_metrics

    except ValueError as ve:
        logger.error(f"Tenant validation error: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found: {str(ve)}"
        )
    except Exception as e:
        logger.error(f"Error getting current usage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/history", response_model=UsageHistoryResponse)
async def get_usage_history(
    months: int = Query(6, ge=1, le=12, description="Number of months to retrieve (1-12)"),
    current_user: dict = Depends(get_current_user),
    usage_service: UsageService = Depends(get_usage_service)
):
    """
    Get usage history for last N months

    Args:
        months: Number of months to retrieve (1-12, default: 6)

    Returns:
        UsageHistoryResponse: Historical usage data for specified months
    """
    try:
        tenant_id = current_user["tenant_id"]
        logger.info(f"Getting {months} months usage history for tenant {tenant_id}")

        history_response = usage_service.get_usage_history(
            tenant_id=tenant_id,
            months=months
        )

        logger.info(f"Retrieved {history_response.total_months} months of usage history")
        return history_response

    except ValueError as ve:
        logger.error(f"Parameter validation error: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter: {str(ve)}"
        )
    except Exception as e:
        logger.error(f"Error getting usage history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/check-limit", response_model=UsageCheckResponse)
async def check_usage_limit(
    request: UsageCheckRequest,
    current_user: dict = Depends(get_current_user),
    usage_service: UsageService = Depends(get_usage_service)
):
    """
    Check if tenant can perform action based on plan limits

    Args:
        request: UsageCheckRequest with resource_type ("leads", "calls", "students")

    Returns:
        UsageCheckResponse: Indicates if action is allowed with usage details
    """
    try:
        tenant_id = current_user["tenant_id"]
        logger.info(f"Checking {request.resource_type} limit for tenant {tenant_id}")

        limit_response = usage_service.check_limit(
            tenant_id=tenant_id,
            resource_type=request.resource_type
        )

        logger.info(f"Limit check result: {limit_response.message}")
        return limit_response

    except ValueError as ve:
        logger.error(f"Resource validation error: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resource type: {str(ve)}"
        )
    except Exception as e:
        logger.error(f"Error checking usage limit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/plans/{plan}", response_model=PlanLimits)
async def get_plan_limits(
    plan: Literal["Starter", "Growth", "Enterprise"] = Path(..., description="Subscription plan name"),
    usage_service: UsageService = Depends(get_usage_service)
):
    """
    Get limits and pricing for specific subscription plan

    Args:
        plan: Plan name ("Starter", "Growth", "Enterprise")

    Returns:
        PlanLimits: Plan configuration with limits and pricing
    """
    try:
        logger.info(f"Getting limits for plan {plan}")

        plan_limits = usage_service.get_plan_limits(plan=plan)

        logger.info(f"Retrieved limits for plan {plan}")
        return plan_limits

    except ValueError as ve:
        logger.error(f"Plan validation error: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {str(ve)}"
        )
    except Exception as e:
        logger.error(f"Error getting plan limits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for usage tracking module

    Returns:
        HealthResponse: Status, module name, and current timestamp
    """
    try:
        return HealthResponse(
            status="healthy",
            module="usage",
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Usage module health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


__all__ = ["router"]