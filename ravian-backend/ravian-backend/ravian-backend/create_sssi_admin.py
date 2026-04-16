from uuid import UUID
from app.core.database import get_session
from app.core.auth import hash_password
from app.models import User, UserRole

def create_admin():
    db = get_session()
    try:
        tenant_id = UUID("8a19c99f-3ebe-4c47-b483-b8796d122716")
        email = "admin@sssi.in"
        password = "password123"

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print("Admin user already exists.")
            return

        new_user = User(
            email=email,
            password_hash=hash_password(password),
            first_name="SSSI",
            last_name="Admin",
            role=UserRole.ADMIN,
            tenant_id=tenant_id
        )
        db.add(new_user)
        db.commit()
        print(f"Created Admin! Email: {email} | Password: {password}")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
