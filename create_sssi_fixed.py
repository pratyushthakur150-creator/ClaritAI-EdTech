import psycopg2
from psycopg2.extras import register_uuid
import uuid

SSSI_TENANT_ID = "8a19c99f-3ebe-4c47-b483-b8796d122716"

conn = psycopg2.connect(
    host="monorail.proxy.rlwy.net",
    port=56117,
    user="postgres",
    password="FWihenwosrWKjIeGXJJTQjwnVZYwbsLx",
    dbname="railway",
    connect_timeout=10
)
register_uuid()
cur = conn.cursor()

# Check if already exists
cur.execute("SELECT id, name FROM tenants WHERE id = %s", (uuid.UUID(SSSI_TENANT_ID),))
existing = cur.fetchone()

if existing:
    print(f"Tenant already exists: {existing[1]} ({existing[0]})")
else:
    cur.execute("""
        INSERT INTO tenants (id, name, domain, subscription_plan, branding, credits_remaining, is_deleted, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s::jsonb, 1000, false, NOW(), NOW())
    """, (
        uuid.UUID(SSSI_TENANT_ID),
        "SSSi Online Tutoring",
        "sssi.in",
        "ENTERPRISE",
        '{"contact_email": "admin@sssi.in", "contact_phone": "+91-742-867-2376"}'
    ))
    conn.commit()
    print("-------------------------------------------")
    print("SUCCESS! SSSi Tenant created in production.")
    print(f"Tenant ID: {SSSI_TENANT_ID}")
    print("Name:      SSSi Online Tutoring")
    print("Domain:    sssi.in")
    print("Plan:      ENTERPRISE")
    print("-------------------------------------------")

conn.close()
