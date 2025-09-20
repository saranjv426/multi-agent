"""
Database Connection Management for Railway PostgreSQL
Handles SQLAlchemy database sessions and connection pooling
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from .models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self, database_url: str):
        """Initialize database manager with connection URL"""
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
    
    def _setup_engine(self):
        """Set up SQLAlchemy engine with optimal settings for Railway"""
        try:
            # Create engine with connection pooling
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=5,  # Small pool for Railway's connection limits
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,  # Recycle connections every 30 minutes
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("Database engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session (dependency injection for FastAPI)"""
        session = self.SessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            from sqlalchemy import text
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

# Global database manager instance
db_manager = None

def get_database_manager() -> DatabaseManager:
    """Get or create database manager instance"""
    global db_manager
    
    if db_manager is None:
        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Railway PostgreSQL URLs sometimes need modification
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        db_manager = DatabaseManager(database_url)
        
    return db_manager

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions"""
    yield from get_database_manager().get_session()

def init_database():
    """Initialize database (create tables, etc.)"""
    manager = get_database_manager()
    manager.create_tables()
    return manager.test_connection()
