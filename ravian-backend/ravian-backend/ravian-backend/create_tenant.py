"""
Utility script to ensure the primary ClariAI tenant exists.

Run this once (from the backend root directory) after the database
is migrated/created:

    uvicorn is NOT required to run for this script.

Example:

    python create_tenant.py
"""

from uuid import UUID

from app.core.database import session_scope
from app.models.tenant import Tenant, SubscriptionPlan


TENANT_ID = UUID("5ebe1c0f-da40-466a-8ed8-5338ecb5033a")


def ensure_tenant() -> None:
    """Create the ClariAI tenant if it doesn't already exist."""
    with session_scope() as session:
        existing = session.query(Tenant).filter(Tenant.id == TENANT_ID).first()
        if existing:
            print(f"✓ Tenant already exists: {existing.id} - {existing.name}")
            return

        tenant = Tenant(
            id=TENANT_ID,
            name="ClariAI Institute",
            domain="clariai.edu",
            subscription_plan=SubscriptionPlan.ENTERPRISE,
            branding={
                "contact_email": "admin@clariai.edu",
                "contact_phone": "+918905538374",
            },
        )

        session.add(tenant)
        print(f"✓ Tenant created: {tenant.id} - {tenant.name}")


if __name__ == "__main__":
    ensure_tenant()

