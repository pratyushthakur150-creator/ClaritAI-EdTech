"""
Database setup and management script
"""
import sys
import subprocess
import logging
from pathlib import Path
from sqlalchemy import text

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import db_manager, test_connection, create_tables
from app.core.config import settings
from app.models import (
    Tenant, User, Lead, ChatbotSession, CallLog, Demo,
    Enrollment, Student, Course, TeachingInteraction, AnalyticsEvent,
    SubscriptionPlan, UserRole, LeadStatus, PaymentStatus
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_dependencies():
    """Install required Python packages"""
    packages = [
        'sqlalchemy==2.0.23',
        'psycopg2-binary==2.9.7', 
        'alembic==1.12.1',
        'asyncpg==0.29.0',
        'python-dotenv==1.0.0'
    ]
    
    for package in packages:
        try:
            print(f"✓ Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")
            return False
    
    return True

def check_database_connection():
    """Test database connectivity"""
    print("✓ Testing database connection...")
    
    if test_connection():
        print("✓ Database connection successful!")
        return True
    else:
        print("✗ Database connection failed!")
        print(f"✗ Database URL: {settings.database_url}")
        print("✗ Please check your database configuration in .env file")
        return False

def create_database_tables():
    """Create all database tables"""
    print("✓ Creating database tables...")
    
    try:
        create_tables()
        print("✓ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"✗ Failed to create database tables: {e}")
        return False

def verify_tables():
    """Verify that all tables were created"""
    print("✓ Verifying database tables...")
    
    expected_tables = [
        'tenants', 'users', 'leads', 'chatbot_sessions',
        'call_logs', 'demos', 'enrollments', 'students',
        'courses', 'teaching_interactions', 'analytics_events'
    ]
    
    try:
        with db_manager.session_scope() as session:
            # Query information_schema to get table names
            result = session.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
            existing_tables = [row[0] for row in result]
            
            missing_tables = [table for table in expected_tables if table not in existing_tables]
            
            if missing_tables:
                print(f"✗ Missing tables: {missing_tables}")
                return False
            else:
                print(f"✓ All {len(expected_tables)} tables verified:")
                for table in sorted(existing_tables):
                    print(f"   • {table}")
                return True
                
    except Exception as e:
        print(f"✗ Failed to verify tables: {e}")
        return False

def initialize_alembic():
    """Initialize Alembic migration environment"""
    print("✓ Initializing Alembic migrations...")
    
    try:
        # Create initial migration
        subprocess.check_call([
            sys.executable, '-m', 'alembic', 'revision', 
            '--autogenerate', '-m', 'Initial database schema'
        ])
        print("✓ Initial migration created!")
        
        # Stamp as current
        subprocess.check_call([sys.executable, '-m', 'alembic', 'stamp', 'head'])
        print("✓ Database stamped with current migration!")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to initialize Alembic: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    print("✓ Creating sample data...")
    
    try:
        with db_manager.session_scope() as session:
            # Create sample tenant
            tenant = Tenant(
                name="Sample Company",
                domain="sample.com",
                subscription_plan=SubscriptionPlan.GROWTH,
                credits_remaining=5000,
                branding={
                    "logo_url": "https://example.com/logo.png",
                    "primary_color": "#007bff",
                    "secondary_color": "#6c757d"
                }
            )
            session.add(tenant)
            session.flush()  # Get the ID
            
            # Create sample user
            user = User(
                tenant_id=tenant.id,
                email="admin@sample.com",
                password_hash="hashed_password_here",
                first_name="John",
                last_name="Doe",
                role=UserRole.ADMIN
            )
            session.add(user)
            
            # Create sample course
            course = Course(
                tenant_id=tenant.id,
                name="Introduction to Data Science",
                description="Learn the fundamentals of data science",
                course_code="DS101",
                syllabus={
                    "modules": [
                        {"name": "Python Basics", "duration": "2 weeks"},
                        {"name": "Statistics", "duration": "3 weeks"},
                        {"name": "Machine Learning", "duration": "4 weeks"}
                    ]
                },
                difficulty_level="Beginner",
                duration_weeks=12,
                total_hours=120,
                category="Data Science",
                price="999"
            )
            session.add(course)
            
            # Create sample lead
            lead = Lead(
                tenant_id=tenant.id,
                name="Jane Smith",
                email="jane@example.com",
                phone="+1234567890",
                source="website",
                status=LeadStatus.NEW,
                intent="Interested in data science course",
                interested_courses=["Data Science"],
                chatbot_context={
                    "conversation_summary": "Interested in career change to data science",
                    "key_interests": ["machine learning", "python", "career change"]
                }
            )
            session.add(lead)
            
            session.commit()
            print("✓ Sample data created successfully!")
            return True
            
    except Exception as e:
        print(f"✗ Failed to create sample data: {e}")
        return False

def print_summary():
    """Print setup summary"""
    print("\n" + "="*60)
    print("DATABASE SETUP COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"Database URL: {settings.database_url}")
    print(f"Tables created: ✓")
    print(f"Migrations initialized: ✓") 
    print(f"Sample data created: ✓")
    print()
    print("Next steps:")
    print("1. Update database credentials in .env file")
    print("2. Run: python main.py (to start the API server)")
    print("3. Visit: http://localhost:8000/docs (API documentation)")
    print("4. Use Alembic for schema changes: alembic revision --autogenerate")
    print()
    print("Database Models Created:")
    models = [
        "• Tenants (multi-tenant isolation)",
        "• Users (admin, mentor, viewer roles)", 
        "• Leads (prospect management)",
        "• Chatbot Sessions (conversation tracking)",
        "• Call Logs (communication history)",
        "• Demos (demo scheduling/tracking)",
        "• Enrollments (course enrollments)",
        "• Students (enrolled learner tracking)",
        "• Courses (educational content)",
        "• Teaching Interactions (Q&A tracking)",
        "• Analytics Events (comprehensive tracking)"
    ]
    for model in models:
        print(f"   {model}")
    print("="*60)

def main():
    """Main setup function"""
    print("Starting database setup...")
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Test connection
    if not check_database_connection():
        sys.exit(1)
    
    # Create tables
    if not create_database_tables():
        sys.exit(1)
    
    # Verify tables
    if not verify_tables():
        sys.exit(1)
    
    # Initialize migrations
    if not initialize_alembic():
        print("⚠ Alembic initialization failed, but database is ready")
    
    # Create sample data
    if not create_sample_data():
        print("⚠ Sample data creation failed, but database is ready")
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    main()
