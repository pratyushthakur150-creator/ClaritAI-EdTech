from uuid import uuid4
from app.core.database import session_scope
from app.models.tenant import Tenant, SubscriptionPlan

def ensure_sssi_tenant() -> None:
    """Create the SSSI tenant."""
    new_id = uuid4()
    with session_scope() as session:
        tenant = Tenant(
            id=new_id,
            name="SSSi Online Tutoring",
            domain="sssi.in",
            subscription_plan=SubscriptionPlan.ENTERPRISE,
            branding={
                "contact_email": "admin@sssi.in",
                "contact_phone": "+91-742-867-2376",
            },
        )
        session.add(tenant)
        print("---------")
        print(f"SUCCESS! SSSI TENANT CREATED.")
        print(f"YOUR NEW TENANT ID IS: {new_id}")
        print("---------")

if __name__ == "__main__":
    ensure_sssi_tenant()
