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
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='tenants' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(r)
conn.close()
