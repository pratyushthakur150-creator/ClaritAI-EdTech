import psycopg2
from psycopg2.extras import register_uuid
import uuid
import bcrypt

TENANT_ID = "8a19c99f-3ebe-4c47-b483-b8796d122716"
EMAIL = "admin@sssi.in"
PASSWORD = "password123"

# Hash the password with bcrypt
password_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()

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

# Check columns in users table
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print("Users table columns:", cols)

# Check if already exists
cur.execute("SELECT id FROM users WHERE email = %s", (EMAIL,))
if cur.fetchone():
    print("Admin already exists!")
    conn.close()
    exit()

user_id = uuid.uuid4()
cur.execute("""
    INSERT INTO users (id, email, password_hash, first_name, last_name, role, tenant_id, is_active, is_deleted, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, true, false, NOW(), NOW())
""", (
    user_id,
    EMAIL,
    password_hash,
    "SSSI",
    "Admin",
    "ADMIN",
    uuid.UUID(TENANT_ID)
))
conn.commit()
print("-------------------------------------------")
print("SUCCESS! SSSi Admin user created.")
print(f"Email:    {EMAIL}")
print(f"Password: {PASSWORD}")
print(f"User ID:  {user_id}")
print("-------------------------------------------")
conn.close()
