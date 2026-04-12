"""
Workflow Router Implementation
File: /app/routers/v1/workflows.py
"""

import logging
import json
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from typing_extensions import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies.auth import get_current_user
from app.core.database import get_db_session
from app.core.redis_client import get_redis_client
from app.core.utils import get_tenant_id
from app.models.lead import Lead
from app.models.call import CallLog
from app.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class WorkflowTriggerRequest(BaseModel):
    lead_id: UUID
    workflow_type: Literal["call_lead", "demo_reminder", "no_show_followup"]


class WorkflowInfo(BaseModel):
    workflow_type: str
    scheduled_at: datetime
    status: str


class WorkflowStatusResponse(BaseModel):
    lead_id: UUID
    workflows: List[WorkflowInfo]
    call_attempts: int
    last_call: Optional[datetime]


class WorkflowTriggerResponse(BaseModel):
    status: str
    message: str
    lead_id: UUID
    workflow_type: str
    scheduled_at: datetime


class HealthResponse(BaseModel):
    status: str
    module: str


# Initialize workflow service
workflow_service = WorkflowService()


def validate_lead_access(lead_id: UUID, tenant_id: UUID, db: Session) -> Lead:
    """
    Validate that lead exists and belongs to the current tenant
    """
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.tenant_id == tenant_id
    ).first()

    if not lead:
        logger.warning(f"Lead {lead_id} not found or access denied for tenant {tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or access denied"
        )

    return lead


@router.post("/trigger", response_model=WorkflowTriggerResponse)
async def trigger_workflow(
    request: WorkflowTriggerRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Manually trigger a workflow for a lead
    """
    try:
        tenant_id = get_tenant_id(current_user)
        logger.info(f"Triggering workflow {request.workflow_type} for lead {request.lead_id}")

        # Validate lead belongs to tenant
        validate_lead_access(request.lead_id, tenant_id, db)

        result = await workflow_service.trigger_workflow(
            lead_id=request.lead_id,
            workflow_type=request.workflow_type,
            tenant_id=tenant_id
        )

        if not result:
            logger.error(f"Failed to trigger workflow {request.workflow_type} for lead {request.lead_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to trigger workflow"
            )

        response = WorkflowTriggerResponse(
            status="success",
            message=f"Workflow {request.workflow_type} triggered successfully",
            lead_id=request.lead_id,
            workflow_type=request.workflow_type,
            scheduled_at=datetime.utcnow()
        )

        logger.info(f"Successfully triggered workflow {request.workflow_type} for lead {request.lead_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/status/{lead_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    lead_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Check workflow status for a specific lead
    """
    try:
        tenant_id = get_tenant_id(current_user)
        logger.info(f"Getting workflow status for lead {lead_id}")

        # Validate lead belongs to tenant
        validate_lead_access(lead_id, tenant_id, db)

        # Get call history from database
        call_logs = db.query(CallLog).filter(
            CallLog.lead_id == lead_id,
            CallLog.tenant_id == tenant_id
        ).order_by(CallLog.created_at.desc()).all()

        call_attempts = len(call_logs)
        last_call = call_logs[0].created_at if call_logs else None

        # Get scheduled workflows from Redis
        redis_client = get_redis_client()
        workflows = []

        try:
            workflow_types = ["call_lead", "demo_reminder", "no_show_followup"]

            for workflow_type in workflow_types:
                redis_key = f"workflow:{tenant_id}:{workflow_type}:{lead_id}"
                workflow_data = redis_client.get(redis_key)

                if workflow_data:
                    try:
                        data = json.loads(workflow_data)
                        workflows.append(WorkflowInfo(
                            workflow_type=workflow_type,
                            scheduled_at=datetime.fromisoformat(
                                data.get('scheduled_at', datetime.utcnow().isoformat())
                            ),
                            status=data.get('status', 'pending')
                        ))
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Error parsing Redis data for key {redis_key}: {str(e)}")
                        continue

        except Exception as redis_error:
            logger.warning(f"Redis error getting workflows for lead {lead_id}: {str(redis_error)}")

        response = WorkflowStatusResponse(
            lead_id=lead_id,
            workflows=workflows,
            call_attempts=call_attempts,
            last_call=last_call
        )

        logger.info(
            f"Retrieved workflow status for lead {lead_id}: "
            f"{call_attempts} calls, {len(workflows)} workflows"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for workflow service
    """
    try:
        return HealthResponse(
            status="healthy",
            module="workflows"
        )
    except Exception as e:
        logger.error(f"Workflow service health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


__all__ = ["router"]