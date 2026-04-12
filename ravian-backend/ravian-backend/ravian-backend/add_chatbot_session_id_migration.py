"""
Database migration script to add chatbot_session_id column to leads table.

Run this script once to add the chatbot_session_id column:
    python add_chatbot_session_id_migration.py
"""

from sqlalchemy import create_engine, text
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add chatbot_session_id column to leads table if it doesn't exist."""
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Check if column already exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='leads' AND column_name='chatbot_session_id'
            """)
            result = conn.execute(check_query)
            exists = result.fetchone() is not None
            
            if exists:
                logger.info("✅ Column 'chatbot_session_id' already exists in 'leads' table")
                return
            
            # Add the column
            logger.info("Adding 'chatbot_session_id' column to 'leads' table...")
            
            # Add column
            add_column_query = text("""
                ALTER TABLE leads 
                ADD COLUMN chatbot_session_id UUID REFERENCES chatbot_sessions(id)
            """)
            conn.execute(add_column_query)
            
            # Create index
            create_index_query = text("""
                CREATE INDEX IF NOT EXISTS ix_leads_chatbot_session_id 
                ON leads(chatbot_session_id)
            """)
            conn.execute(create_index_query)
            
            conn.commit()
            logger.info("✅ Successfully added 'chatbot_session_id' column and index to 'leads' table")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
