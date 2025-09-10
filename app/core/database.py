"""
Database module for centralized database management.
Provides SQLAlchemy integration with FastAPI dependency injection.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from fastapi import Depends
import structlog

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger()

# Create declarative base for SQLAlchemy models
Base = declarative_base()


class DatabaseManager:
    """
    Centralized database management class.
    
    This class is designed to work efficiently in multi-worker and multi-server environments:
    - Each worker process gets its own connection pool
    - Connection pooling is optimized for concurrent access
    - Thread-safe session management
    - Automatic connection cleanup and recycling
    """

    def __init__(
        self,
        driver: str = settings.database_driver,
        host: str = settings.database_host,
        port: int = settings.database_port,
        user: str = settings.database_user,
        password: str = settings.database_password,
        name: str = settings.database_name,
    ):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False

        self.driver = driver
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.name = name
        self.database_url = self.get_database_url()
        logger.info("Database URL", database_url=self.database_url)

    def get_database_url(self) -> str:
        if self.driver == "postgresql+psycopg2":
            formatted_password = self.password.replace("@", "%40")

            return (
                f"postgresql+psycopg2://"
                f"{self.user}"
                f":{formatted_password}"
                f"@{self.host}"
                f":{self.port}"
                f"/{self.name}"
            )
        else:
            raise ValueError(f"Unsupported database driver: {self.driver}")

    def initialize(self) -> None:
        """Initialize the database engine and create tables."""
        if self._initialized:
            logger.info("Database already initialized")
            return

        try:
            # Create engine with connection pooling optimized for multi-worker setup
            self.engine = create_engine(
                self.database_url,
                echo=settings.log_level.upper() == "DEBUG",
                pool_pre_ping=True,
                pool_recycle=300,  # Recycle connections every 5 minutes
                pool_size=5,       # Reduced per-worker pool size for multi-worker setup
                max_overflow=10,   # Reduced overflow for better resource management
                pool_timeout=30,   # Timeout for getting connection from pool
                pool_reset_on_return='commit',  # Reset connections on return
            )

            # Create sessionmaker
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            # Create all tables
            Base.metadata.create_all(self.engine)
            self._initialized = True
            logger.info(
                "Database initialized successfully", database_url=self.database_url
            )

        except Exception as e:
            logger.error(
                "Failed to initialize database",
                error=str(e),
                database_url=self.database_url,
            )
            raise

    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        if not self._initialized:
            self.initialize()

        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            logger.error("Database session error", error=str(e))
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[Session, None]:
        """Get an async database session with automatic cleanup."""
        if not self._initialized:
            self.initialize()

        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            logger.error("Async database session error", error=str(e))
            session.rollback()
            raise
        finally:
            session.close()

    def get_pool_status(self) -> dict:
        """Get connection pool status for monitoring."""
        if not self.engine:
            return {"status": "not_initialized"}
        
        pool = self.engine.pool
        return {
            "status": "active",
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }

    def close(self) -> None:
        """Close the database engine."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine closed")


# Global database manager instance
db_manager = DatabaseManager(
    driver=settings.database_driver,
    host=settings.database_host,
    port=settings.database_port,
    user=settings.database_user,
    password=settings.database_password,
    name=settings.database_name,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for getting database sessions.

    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    yield from db_manager.get_session()


async def get_async_db() -> AsyncGenerator[Session, None]:
    """
    FastAPI dependency for getting async database sessions.

    Usage:
        @app.get("/items/")
        async def read_items(db: Session = Depends(get_async_db)):
            return db.query(Item).all()
    """
    async with db_manager.get_async_session() as session:
        yield session


def init() -> None:
    """Initialize the database connection. Call this during application startup."""
    logger.info("Initializing database")
    db_manager.initialize()


def close() -> None:
    """Close the database connection. Call this during application shutdown."""
    logger.info("Closing database")
    db_manager.close()


# Convenience function for direct database access
def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager


def get_pool_status() -> dict:
    """Get connection pool status for monitoring."""
    return db_manager.get_pool_status()
