"""
Database Connection Management for Railway PostgreSQL
Handles SQLAlchemy database sessions and connection pooling
"""

import os
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from .models import Base

logger = logging.getLogger(__name__)


_SCHEMA_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_schema_name(schema_name: str) -> str:
    """Validate DB schema name to avoid SQL injection and invalid identifiers."""
    normalized = (schema_name or "").strip()
    if not normalized:
        return "public"
    if not _SCHEMA_NAME_PATTERN.match(normalized):
        raise ValueError(
            "DB_SCHEMA must be a valid PostgreSQL identifier "
            "(letters, numbers, underscore; cannot start with a number)"
        )
    return normalized


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self, database_url: str, db_schema: str = "public"):
        """Initialize database manager with connection URL"""
        self.database_url = database_url
        self.db_schema = validate_schema_name(db_schema)
        self._is_postgres = self.database_url.startswith("postgresql://")
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
    
    def _setup_engine(self):
        """Set up SQLAlchemy engine with optimal settings for Railway"""
        try:
            connect_args = {}
            if self._is_postgres:
                # Keep app objects isolated per environment while sharing one DB instance.
                connect_args["options"] = f"-csearch_path={self.db_schema},public"

            # Create engine with connection pooling
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=5,  # Small pool for Railway's connection limits
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,  # Recycle connections every 30 minutes
                connect_args=connect_args,
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

    def _ensure_schema_exists(self):
        """Create schema if missing (PostgreSQL only)."""
        if not self._is_postgres:
            return
        with self.engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.db_schema}"'))
    
    def create_tables(self):
        """Create all database tables"""
        try:
            self._ensure_schema_exists()
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"Database tables created successfully in schema: {self.db_schema}")
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

        db_schema = validate_schema_name(os.getenv("DB_SCHEMA", "public"))
        db_manager = DatabaseManager(database_url, db_schema=db_schema)
        
    return db_manager

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions"""
    yield from get_database_manager().get_session()

def init_database():
    """Initialize database (create tables, etc.)"""
    manager = get_database_manager()
    manager.create_tables()
    return manager.test_connection()
