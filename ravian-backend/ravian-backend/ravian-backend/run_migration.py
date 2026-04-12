"""
Run Teaching Assistant migration.
Usage: python run_migration.py
"""
import os
import sys

# Ensure app is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import psycopg2
except ImportError:
    print("[ERROR] psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

# Load settings for DB connection
try:
    from app.core.config import settings
    conn = psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )
except Exception as e:
    print(f"[ERROR] Database connection failed: {e}")
    print("Using fallback: localhost:5432, dbname=ravian_db, user=postgres, password=ClaritAi")
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="ravian_db",
        user="postgres",
        password="ClaritAi",
    )

conn.autocommit = False
cursor = conn.cursor()

migration_path = os.path.join(os.path.dirname(__file__), "app", "migrations", "teaching_assistant_schema.sql")
if not os.path.exists(migration_path):
    print(f"[ERROR] Migration file not found: {migration_path}")
    sys.exit(1)

with open(migration_path, "r", encoding="utf-8") as f:
    sql = f.read()

try:
    cursor.execute(sql)
    conn.commit()
    print("[OK] Teaching Assistant migration completed successfully")
except Exception as e:
    conn.rollback()
    print(f"[ERROR] Migration failed: {e}")
    raise
finally:
    cursor.close()
    conn.close()
