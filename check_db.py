import psycopg2

try:
    conn = psycopg2.connect(
        host="monorail.proxy.rlwy.net",
        port=56117,
        user="postgres",
        password="FWihenwosrWKjIeGXJJTQjwnVZYwbsLx",
        dbname="railway",
        connect_timeout=10
    )
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = [row[0] for row in cur.fetchall()]
    print(f"Tables found ({len(tables)}):", tables)
    conn.close()
except ImportError:
    print("psycopg2 not installed. Run: pip install psycopg2-binary")
except Exception as e:
    print(f"DB ERROR: {type(e).__name__}: {e}")
