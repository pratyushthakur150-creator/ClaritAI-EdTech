import psycopg2

conn = psycopg2.connect(
    host="monorail.proxy.rlwy.net",
    port=56117,
    user="postgres",
    password="FWihenwosrWKjIeGXJJTQjwnVZYwbsLx",
    dbname="railway",
    connect_timeout=10
)
cur = conn.cursor()
cur.execute("SELECT id, name, domain, subscription_plan FROM tenants")
rows = cur.fetchall()
print(f"Total tenants: {len(rows)}")
for r in rows:
    print("---")
    print(f"ID:     {r[0]}")
    print(f"Name:   {r[1]}")
    print(f"Domain: {r[2]}")
    print(f"Plan:   {r[3]}")
conn.close()
