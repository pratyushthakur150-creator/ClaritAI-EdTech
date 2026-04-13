"""
Database connection and session management
"""
import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database engine and session factory"""
        try:
            # Create database engine
            self.engine = create_engine(
                settings.database_url,
                poolclass=QueuePool,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=settings.db_pool_recycle,
                echo=settings.db_echo,  # Log SQL queries if debug
            )
            
            # Add connection event listeners
            event.listen(self.engine, "connect", self._on_connect)
            event.listen(self.engine, "checkout", self._on_checkout)
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("Database engine and session factory initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _on_connect(self, dbapi_connection, connection_record):
        """Called when a new database connection is created"""
        logger.debug("New database connection established")
        
        # Set PostgreSQL-specific settings
        with dbapi_connection.cursor() as cursor:
            # Set timezone to UTC
            cursor.execute("SET timezone TO 'UTC'")
            
    def _on_checkout(self, dbapi_connection, connection_record, connection_proxy):
        """Called when a connection is retrieved from the pool"""
        logger.debug("Database connection checked out from pool")
    
    def get_session(self) -> Session:
        """Get a new database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around database operations"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all database tables"""
        try:
            from app.models import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            from app.models import Base
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions
from typing import Generator

def get_db_session() -> Generator[Session, None, None]:
    """Get a database session (FastAPI dependency)"""
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()

def get_session() -> Session:
    """Get a database session for direct use"""
    return db_manager.get_session()

@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Session scope context manager"""
    with db_manager.session_scope() as session:
        yield session

def create_tables():
    """Create all database tables"""
    db_manager.create_tables()

def test_connection() -> bool:
    """Test database connection"""
    return db_manager.test_connection()

# Multi-tenant utilities
class TenantSession:
    """Session wrapper with tenant context"""
    
    def __init__(self, session: Session, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id
    
    def query(self, model, **kwargs):
        """Query with automatic tenant filtering"""
        query = self.session.query(model)
        
        # Add tenant filter if model has tenant_id
        if hasattr(model, 'tenant_id'):
            query = query.filter(model.tenant_id == self.tenant_id)
        
        # Add additional filters
        for key, value in kwargs.items():
            if hasattr(model, key):
                query = query.filter(getattr(model, key) == value)
        
        return query
    
    def add(self, instance):
        """Add instance with tenant context"""
        if hasattr(instance, 'tenant_id') and not instance.tenant_id:
            instance.tenant_id = self.tenant_id
        return self.session.add(instance)
    
    def commit(self):
        """Commit session"""
        return self.session.commit()
    
    def rollback(self):
        """Rollback session"""
        return self.session.rollback()
    
    def close(self):
        """Close session"""
        return self.session.close()

@contextmanager
def tenant_session_scope(tenant_id: str) -> Generator[TenantSession, None, None]:
    """Tenant-aware session scope"""
    with session_scope() as session:
        tenant_session = TenantSession(session, tenant_id)
        yield tenant_session
