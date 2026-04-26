import psycopg2
from psycopg2.extras import register_uuid

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
cur.execute("SELECT id, email, role, tenant_id FROM users WHERE email = 'admin@sssi.in'")
row = cur.fetchone()
if row:
    print(f"User EXISTS:")
    print(f"  ID:        {row[0]}")
    print(f"  Email:     {row[1]}")
    print(f"  Role:      {row[2]}")
    print(f"  Tenant ID: {row[3]}")
else:
    print("User NOT FOUND - admin@sssi.in does not exist in DB")
conn.close()
