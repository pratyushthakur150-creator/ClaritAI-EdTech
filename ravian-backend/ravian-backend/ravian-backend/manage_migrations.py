"""
Database migration management script
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n✓ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description} completed successfully")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"✗ {description} failed")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ {description} failed: {e}")
        return False

def create_migration(message="Auto-generated migration"):
    """Create a new migration"""
    cmd = f'alembic revision --autogenerate -m "{message}"'
    return run_command(cmd, f"Creating migration: {message}")

def run_migrations():
    """Run pending migrations"""
    cmd = "alembic upgrade head"
    return run_command(cmd, "Running migrations")

def show_migration_history():
    """Show migration history"""
    cmd = "alembic history --verbose"
    return run_command(cmd, "Showing migration history")

def show_current_revision():
    """Show current database revision"""
    cmd = "alembic current"
    return run_command(cmd, "Checking current database revision")

def downgrade_migration(revision="base"):
    """Downgrade to a specific revision"""
    cmd = f"alembic downgrade {revision}"
    return run_command(cmd, f"Downgrading to revision: {revision}")

def stamp_database(revision="head"):
    """Stamp database with a specific revision"""
    cmd = f"alembic stamp {revision}"
    return run_command(cmd, f"Stamping database with revision: {revision}")

def show_help():
    """Show available commands"""
    print("""
Database Migration Management Script
===================================

Available commands:
  create [message]    - Create a new migration with optional message
  migrate            - Run all pending migrations
  history            - Show migration history
  current            - Show current database revision
  downgrade [rev]    - Downgrade to specific revision (default: base)
  stamp [rev]        - Stamp database with revision (default: head)
  help               - Show this help message

Examples:
  python manage_migrations.py create "Add user profile fields"
  python manage_migrations.py migrate
  python manage_migrations.py downgrade -1
  python manage_migrations.py stamp head
    """)

def main():
    """Main function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "create":
        message = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Auto-generated migration"
        create_migration(message)
    
    elif command == "migrate":
        run_migrations()
    
    elif command == "history":
        show_migration_history()
    
    elif command == "current":
        show_current_revision()
    
    elif command == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "base"
        downgrade_migration(revision)
    
    elif command == "stamp":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        stamp_database(revision)
    
    elif command == "help":
        show_help()
    
    else:
        print(f"Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()
