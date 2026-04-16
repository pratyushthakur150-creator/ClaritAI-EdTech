import psycopg2
import bcrypt
import uuid

conn = psycopg2.connect(
    host="monorail.proxy.rlwy.net",
    port=56117,
    user="postgres",
    password="FWihenwosrWKjIeGXJJTQjwnVZYwbsLx",
    dbname="railway",
    connect_timeout=10
)
cur = conn.cursor()

# Check what enum values are allowed for subscription_plan
cur.execute("SELECT enum_range(NULL::subscriptionplan)")
plans = cur.fetchone()
print("Allowed subscription plans:", plans)

# Check what enum values are allowed for role
cur.execute("SELECT enum_range(NULL::userrole)")
roles = cur.fetchone()
print("Allowed user roles:", roles)

# Find or create tenant
cur.execute("SELECT id FROM tenants WHERE name = %s", ("Ravian EdTech",))
row = cur.fetchone()
if row:
    tenant_id = str(row[0])
    print(f"\nUsing existing tenant: {tenant_id}")
else:
    tenant_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO tenants (id, name, domain, subscription_plan, credits_remaining, is_deleted) 
        VALUES (%s, %s, %s, 'STARTER', 1000, false)
        RETURNING id
    """, (tenant_id, "Ravian EdTech", "ravian-edtech.ravian.com"))
    tenant_id = str(cur.fetchone()[0])
    print(f"\nCreated tenant: {tenant_id}")

# Create admin user
password = "RavianAdmin2024!"
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

user_id = str(uuid.uuid4())
cur.execute("""
    INSERT INTO users (id, email, password_hash, first_name, last_name, role, tenant_id, is_active, is_deleted) 
    VALUES (%s, %s, %s, %s, %s, 'ADMIN', %s, true, false)
    RETURNING id
""", (user_id, "admin@ravian.com", password_hash, "Pratyush", "Thakur", tenant_id))

result = cur.fetchone()
if result:
    print(f"Created admin user: {result[0]}")
else:
    print("Admin user already exists")

conn.commit()
conn.close()
print("\nDone! Login with:")
print("  Email: admin@ravian.com")
print("  Password: RavianAdmin2024!")
