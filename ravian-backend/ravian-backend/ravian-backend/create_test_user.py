from app.core.database import get_session
from app.core.auth import hash_password
from app.models import User, Tenant, UserRole


def main() -> None:
    db = get_session()
    try:
        email = "test@ravian.com"
        password = "Test123456"

        # Ensure tenant exists
        tenant_name = "Ravian EdTech"
        domain = f"{tenant_name.lower().replace(' ', '-')}.ravian.com"

        tenant = db.query(Tenant).filter(Tenant.name == tenant_name).first()
        if not tenant:
            tenant = Tenant(name=tenant_name, domain=domain)
            db.add(tenant)
            db.flush()  # get tenant.id

        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print("Test user already exists")
        else:
            new_user = User(
                email=email,
                password_hash=hash_password(password),
                first_name="Test",
                last_name="User",
                role=UserRole.VIEWER,
                tenant_id=tenant.id,
            )
            db.add(new_user)
            db.commit()
            print("Test user created successfully")
    except Exception as e:
        db.rollback()
        print(f"Failed to create test user: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

