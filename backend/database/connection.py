"""
Database connection management.
Supports PostgreSQL in deployed environments and SQLite fallback for local development.
"""

import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from .models import Base

logger = logging.getLogger(__name__)


_SCHEMA_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def get_local_sqlite_url() -> str:
    """Return the SQLite URL used for local development fallback."""
    configured = os.getenv("LOCAL_DATABASE_URL", "").strip()
    if configured:
        return configured

    db_path = Path(__file__).resolve().parent.parent / "local_dev.db"
    return f"sqlite:///{db_path}"


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


def postgres_sslmode(database_url: str) -> str:
    """Return the SSL mode to use for PostgreSQL connections."""
    configured = os.getenv("DB_SSLMODE", "").strip()
    if configured:
        return configured

    # Cloud Postgres providers such as Render expect SSL. Keep local Postgres
    # developer-friendly unless the caller explicitly opts in with DB_SSLMODE.
    if any(host in database_url for host in ("localhost", "127.0.0.1", "::1")):
        return "prefer"
    return "require"


def describe_database_url(database_url: str) -> str:
    """Return a safe database URL summary for logs."""
    parsed = urlparse(database_url)
    host = parsed.hostname or "unknown-host"
    port = parsed.port or 5432
    database = parsed.path.lstrip("/") or "unknown-db"
    return f"{parsed.scheme}://{host}:{port}/{database}"


def is_render_external_postgres_url(database_url: str) -> bool:
    """Detect Render's public Postgres hostnames."""
    host = urlparse(database_url).hostname or ""
    return host.endswith("-postgres.render.com")


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
                connect_args["sslmode"] = postgres_sslmode(self.database_url)
                logger.info(
                    "PostgreSQL target: %s, schema=%s, sslmode=%s",
                    describe_database_url(self.database_url),
                    self.db_schema,
                    connect_args["sslmode"],
                )
                if (
                    os.getenv("ENVIRONMENT", "development").lower() == "production"
                    and is_render_external_postgres_url(self.database_url)
                ):
                    logger.warning(
                        "DATABASE_URL appears to use Render's external Postgres host. "
                        "For a Render web service in the same account and region as the database, "
                        "use the Internal Database URL instead."
                    )
            elif self.database_url.startswith("sqlite"):
                connect_args["check_same_thread"] = False

            # Create engine with connection pooling
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=5,  # Small pool for Railway's connection limits
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,  # Recycle connections every 30 minutes
                pool_pre_ping=True,
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
            environment = os.getenv("ENVIRONMENT", "development").lower()
            if environment == "development":
                database_url = get_local_sqlite_url()
                logger.warning(
                    "DATABASE_URL not set; using local SQLite database for development: %s",
                    database_url,
                )
            else:
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
    global db_manager
    manager = get_database_manager()
    max_attempts = max(1, int(os.getenv("DB_INIT_MAX_ATTEMPTS", "5")))
    retry_delay = max(0.0, float(os.getenv("DB_INIT_RETRY_DELAY_SECONDS", "3")))

    try:
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                manager.create_tables()
                return manager.test_connection()
            except OperationalError as exc:
                last_error = exc
                if attempt >= max_attempts:
                    raise
                logger.warning(
                    "Database initialization attempt %s/%s failed; retrying in %.1fs: %s",
                    attempt,
                    max_attempts,
                    retry_delay,
                    exc,
                )
                time.sleep(retry_delay)
        if last_error:
            raise last_error
        return False
    except OperationalError as exc:
        environment = os.getenv("ENVIRONMENT", "development").lower()
        fallback_enabled = os.getenv("ENABLE_SQLITE_FALLBACK", "true").lower() == "true"

        if environment != "development" or not fallback_enabled or not manager._is_postgres:
            raise

        fallback_url = get_local_sqlite_url()
        logger.warning(
            "Primary PostgreSQL database is unavailable in development; "
            "falling back to SQLite at %s. Original error: %s",
            fallback_url,
            exc,
        )
        db_manager = DatabaseManager(fallback_url, db_schema="public")
        db_manager.create_tables()
        return db_manager.test_connection()
