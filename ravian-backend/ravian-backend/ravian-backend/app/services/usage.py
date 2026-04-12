"""
Usage Service Implementation
File: /app/services/usage_service.py
"""

import logging
import redis
from datetime import datetime, timedelta
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.schemas.usage import UsageMetrics, UsageCheckResponse, UsageHistoryResponse, PlanLimits
from app.models.tenant import Tenant, SubscriptionPlan
from app.models.enrollment import Student

logger = logging.getLogger(__name__)

# Plan limits configuration — keys match SubscriptionPlan enum values (lowercase)
PLAN_LIMITS = {
    "starter": {
        "leads": 500,
        "calls": 200,
        "students": 50,
        "credits": 1000,
        "price": 99.0
    },
    "growth": {
        "leads": 2000,
        "calls": 1000,
        "students": 200,
        "credits": 5000,
        "price": 299.0
    },
    "enterprise": {
        "leads": 999999,
        "calls": 999999,
        "students": 999999,
        "credits": 999999,
        "price": 999.0
    },
    "admin": {
        "leads": 999999,
        "calls": 999999,
        "students": 999999,
        "credits": 999999,
        "price": 0.0
    }
}

# Map enum values to schema Literal values for response
PLAN_DISPLAY_MAP = {
    "starter": "Starter",
    "growth": "Growth",
    "enterprise": "Enterprise",
    "admin": "Enterprise"  # admin maps to Enterprise tier for display
}


class UsageService:
    """Service for tracking and managing tenant resource usage"""

    def __init__(self, db: Session, redis_client: redis.Redis):
        """
        Initialize UsageService with database session and Redis client

        Args:
            db: SQLAlchemy database session
            redis_client: Redis client instance
        """
        self.db = db
        self.redis_client = redis_client
        logger.info("UsageService initialized")

    def _get_plan_key(self, tenant: Tenant) -> str:
        """
        Extract lowercase plan key from tenant's SubscriptionPlan enum

        Args:
            tenant: Tenant model instance

        Returns:
            Lowercase plan key string
        """
        plan_value = tenant.subscription_plan
        if isinstance(plan_value, SubscriptionPlan):
            return plan_value.value.lower()
        if isinstance(plan_value, str):
            return plan_value.lower()
        return "starter"

    def get_current_usage(self, tenant_id: UUID) -> UsageMetrics:
        """
        Get current month usage metrics for a tenant

        Args:
            tenant_id: UUID of the tenant

        Returns:
            UsageMetrics object with current usage data

        Raises:
            ValueError: If tenant not found
        """
        try:
            logger.info(f"Getting current usage for tenant {tenant_id}")

            tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                logger.error(f"Tenant {tenant_id} not found")
                raise ValueError(f"Tenant {tenant_id} not found")

            plan_key = self._get_plan_key(tenant)
            if plan_key not in PLAN_LIMITS:
                logger.warning(f"Unknown plan key '{plan_key}' for tenant {tenant_id}, defaulting to starter")
                plan_key = "starter"

            # Current month period
            current_month = datetime.utcnow().strftime("%Y-%m")

            # Get usage counters from Redis
            leads_key = f"usage:{tenant_id}:leads:{current_month}"
            calls_key = f"usage:{tenant_id}:calls:{current_month}"
            credits_key = f"usage:{tenant_id}:credits:{current_month}"

            leads_created = int(self.redis_client.get(leads_key) or 0)
            calls_made = int(self.redis_client.get(calls_key) or 0)
            credits_consumed = float(self.redis_client.get(credits_key) or 0)

            # Count active students from last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            active_students = self.db.query(func.count(Student.id)).filter(
                and_(
                    Student.tenant_id == tenant_id,
                    Student.last_active >= thirty_days_ago
                )
            ).scalar() or 0

            plan_config = PLAN_LIMITS[plan_key]
            plan_display = PLAN_DISPLAY_MAP.get(plan_key, "Starter")

            usage_metrics = UsageMetrics(
                tenant_id=tenant_id,
                period=current_month,
                leads_created=leads_created,
                leads_limit=plan_config["leads"],
                calls_made=calls_made,
                calls_limit=plan_config["calls"],
                active_students=active_students,
                students_limit=plan_config["students"],
                credits_consumed=credits_consumed,
                credits_limit=plan_config["credits"],
                plan=plan_display
            )

            logger.info(
                f"Retrieved usage for tenant {tenant_id}: "
                f"{leads_created} leads, {calls_made} calls, {active_students} students"
            )
            return usage_metrics

        except Exception as e:
            logger.error(f"Error getting current usage for tenant {tenant_id}: {str(e)}")
            raise

    def get_usage_history(self, tenant_id: UUID, months: int = 6) -> UsageHistoryResponse:
        """
        Get usage history for the last N months

        Args:
            tenant_id: UUID of the tenant
            months: Number of months to retrieve (default: 6)

        Returns:
            UsageHistoryResponse with historical usage data
        """
        try:
            logger.info(f"Getting {months} months usage history for tenant {tenant_id}")

            tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                logger.error(f"Tenant {tenant_id} not found")
                raise ValueError(f"Tenant {tenant_id} not found")

            plan_key = self._get_plan_key(tenant)
            if plan_key not in PLAN_LIMITS:
                logger.warning(f"Unknown plan key '{plan_key}' for tenant {tenant_id}, defaulting to starter")
                plan_key = "starter"

            plan_config = PLAN_LIMITS[plan_key]
            plan_display = PLAN_DISPLAY_MAP.get(plan_key, "Starter")
            history = []

            # Generate months list (current month backwards)
            current_date = datetime.utcnow()
            for i in range(months):
                month_date = current_date.replace(day=1) - timedelta(days=i * 30)
                period = month_date.strftime("%Y-%m")

                leads_key = f"usage:{tenant_id}:leads:{period}"
                calls_key = f"usage:{tenant_id}:calls:{period}"
                credits_key = f"usage:{tenant_id}:credits:{period}"

                leads_created = int(self.redis_client.get(leads_key) or 0)
                calls_made = int(self.redis_client.get(calls_key) or 0)
                credits_consumed = float(self.redis_client.get(credits_key) or 0)

                # Historical student count not tracked per-month
                active_students = 0

                usage_metrics = UsageMetrics(
                    tenant_id=tenant_id,
                    period=period,
                    leads_created=leads_created,
                    leads_limit=plan_config["leads"],
                    calls_made=calls_made,
                    calls_limit=plan_config["calls"],
                    active_students=active_students,
                    students_limit=plan_config["students"],
                    credits_consumed=credits_consumed,
                    credits_limit=plan_config["credits"],
                    plan=plan_display
                )

                history.append(usage_metrics)

            response = UsageHistoryResponse(
                history=history,
                total_months=len(history)
            )

            logger.info(f"Retrieved {len(history)} months of usage history for tenant {tenant_id}")
            return response

        except Exception as e:
            logger.error(f"Error getting usage history for tenant {tenant_id}: {str(e)}")
            raise

    def check_limit(self, tenant_id: UUID, resource_type: str) -> UsageCheckResponse:
        """
        Check if tenant can perform action based on plan limits

        Args:
            tenant_id: UUID of the tenant
            resource_type: Type of resource ("leads", "calls", "students")

        Returns:
            UsageCheckResponse indicating if action is allowed
        """
        try:
            logger.info(f"Checking {resource_type} limit for tenant {tenant_id}")

            if resource_type not in ["leads", "calls", "students"]:
                raise ValueError(f"Invalid resource type: {resource_type}")

            current_usage = self.get_current_usage(tenant_id)

            usage_map = {
                "leads": (current_usage.leads_created, current_usage.leads_limit),
                "calls": (current_usage.calls_made, current_usage.calls_limit),
                "students": (current_usage.active_students, current_usage.students_limit)
            }

            current_count, limit = usage_map[resource_type]
            remaining = max(0, limit - current_count)
            allowed = current_count < limit

            if allowed:
                message = f"{resource_type.capitalize()} usage: {current_count}/{limit} ({remaining} remaining)"
            else:
                message = f"{resource_type.capitalize()} limit exceeded: {current_count}/{limit}"

            response = UsageCheckResponse(
                allowed=allowed,
                current_usage=current_count,
                limit=limit,
                remaining=remaining,
                message=message,
                upgrade_required=not allowed and current_usage.plan != "Enterprise"
            )

            logger.info(
                f"Limit check for {resource_type}: {current_count}/{limit} - "
                f"{'Allowed' if allowed else 'Blocked'}"
            )
            return response

        except Exception as e:
            logger.error(f"Error checking {resource_type} limit for tenant {tenant_id}: {str(e)}")
            raise

    def increment_usage(self, tenant_id: UUID, resource_type: str, count: int = 1):
        """
        Increment usage counter in Redis.
        Never raises — usage tracking failure must not block operations.

        Args:
            tenant_id: UUID of the tenant
            resource_type: Type of resource ("leads", "calls", "credits")
            count: Amount to increment (default: 1)
        """
        try:
            current_month = datetime.utcnow().strftime("%Y-%m")
            redis_key = f"usage:{tenant_id}:{resource_type}:{current_month}"

            new_value = self.redis_client.incrby(redis_key, count)

            # Set 90-day expiry on first write
            if new_value == count:
                self.redis_client.expire(redis_key, 90 * 24 * 60 * 60)

            logger.info(
                f"Incremented {resource_type} usage for tenant {tenant_id}: "
                f"+{count} (total: {new_value})"
            )

        except Exception as e:
            logger.error(
                f"Error incrementing {resource_type} usage for tenant {tenant_id}: {str(e)}"
            )

    def get_plan_limits(self, plan: str) -> PlanLimits:
        """
        Get plan limits for a specific plan

        Args:
            plan: Plan name ("Starter", "Growth", "Enterprise")

        Returns:
            PlanLimits object with plan configuration

        Raises:
            ValueError: If plan is not recognized
        """
        try:
            plan_key = plan.lower()
            if plan_key not in PLAN_LIMITS:
                logger.error(f"Unknown plan: {plan}")
                raise ValueError(f"Unknown plan: {plan}")

            config = PLAN_LIMITS[plan_key]
            plan_display = PLAN_DISPLAY_MAP.get(plan_key, "Starter")

            plan_limits = PlanLimits(
                plan=plan_display,
                leads_limit=config["leads"],
                calls_limit=config["calls"],
                students_limit=config["students"],
                credits_limit=config["credits"],
                price_per_month=config["price"]
            )

            logger.info(f"Retrieved limits for plan {plan}")
            return plan_limits

        except Exception as e:
            logger.error(f"Error getting plan limits for {plan}: {str(e)}")
            raise


__all__ = ["UsageService", "PLAN_LIMITS"]