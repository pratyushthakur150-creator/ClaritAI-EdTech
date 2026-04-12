"""
Workflow Service

Lightweight service layer used by the workflow router to orchestrate
background actions such as calling leads or sending reminders.

The current implementation focuses on providing a stable interface for
the API layer and logging workflow triggers. Business logic can be
extended here without changing the router contracts.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from redis import Redis


logger = logging.getLogger(__name__)


class WorkflowService:
    """
    Service class for workflow orchestration.

    NOTE: The router only relies on this service to expose a
    `trigger_workflow` coroutine that returns a truthy value on success.
    This implementation keeps behavior simple and side‑effect safe while
    allowing future extension.
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        redis_client: Optional[Redis] = None,
    ) -> None:
        self.db = db
        self.redis_client = redis_client
        self.logger = logger

    async def trigger_workflow(
        self,
        lead_id: UUID,
        workflow_type: str,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """
        Trigger a workflow for a given lead.

        Current behavior:
        - Logs the trigger request
        - Returns a simple payload describing the scheduled workflow
        """
        self.logger.info(
            "Triggering workflow",
            extra={
                "workflow_type": workflow_type,
                "lead_id": str(lead_id),
                "tenant_id": str(tenant_id),
                "scheduled_at": datetime.utcnow().isoformat(),
            },
        )

        # Placeholder for future queueing / scheduling logic
        # (e.g. pushing to Redis or task queue)

        return {
            "lead_id": lead_id,
            "workflow_type": workflow_type,
            "tenant_id": tenant_id,
            "scheduled_at": datetime.utcnow(),
        }

