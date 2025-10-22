"""
Database module for PostgreSQL with comprehensive session management.

This module provides:
- Database engine and session factory
- Session decorators for easy use in APIs and MQTT consumers
- Context managers for manual session handling
- Database health checks and connection management
- Automatic transaction management with rollback on exceptions
"""

import functools
from contextlib import contextmanager
from typing import Any, Callable, Generator, Optional, TypeVar
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import QueuePool

from app.core.config import settings
from app.core.logging import logger


F = TypeVar('F', bound=Callable[..., Any])
AsyncF = TypeVar('AsyncF', bound=Callable[..., Any])


Base = declarative_base()


_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None
_scoped_session_factory: Optional[scoped_session] = None

DATABASE_URL = (
    f"{settings.DATABASE_DRIVER}"
    f"://{settings.DATABASE_USER}"
    f":{settings.DATABASE_PASSWORD}"
    f"@{settings.DATABASE_HOST}"
    f":{settings.DATABASE_PORT}"
    f"/{settings.DATABASE_NAME}"
)


def get_engine() -> Engine:
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=settings.LOG_LEVEL.upper() == "DEBUG",
            echo_pool=settings.LOG_LEVEL.upper() == "DEBUG",
        )
        
        # Add connection event listeners
        @event.listens_for(_engine, "connect")
        def set_postgresql_timezone(dbapi_connection, connection_record):
            """Set PostgreSQL timezone for each connection."""
            with dbapi_connection.cursor() as cursor:
                cursor.execute(f"SET timezone TO '{settings.DATABASE_TIMEZONE}'")
        
        @event.listens_for(_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log when a connection is checked out from the pool."""
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log when a connection is checked in to the pool."""
            logger.debug("Connection checked in to pool")
    
    return _engine


def get_session_factory() -> sessionmaker:
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
    return _session_factory


def get_scoped_session_factory() -> scoped_session:
    """Get or create the scoped session factory for thread-safe operations."""
    global _scoped_session_factory
    if _scoped_session_factory is None:
        _scoped_session_factory = scoped_session(get_session_factory())
    return _scoped_session_factory


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for getting a database session.
    
    Usage in FastAPI endpoints:
        @app.get("/users/")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    session = get_session_factory()()
    try:
        yield session
    except Exception as e:
        logger.error("Database session error", error=str(e), exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic transaction management.
    
    Usage:
        with get_db_session() as db:
            user = User(name="John")
            db.add(user)
            db.commit()
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error("Database session error", error=str(e), exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_db_session_manual() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with manual transaction management.
    
    Usage:
        with get_db_session_manual() as db:
            user = User(name="John")
            db.add(user)
            # You must manually commit or rollback
            db.commit()
    """
    session = get_session_factory()()
    try:
        yield session
    except Exception as e:
        logger.error("Database session error", error=str(e), exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()


def with_db_session(func: F) -> F:
    """
    Decorator for functions that need a database session with automatic transaction management.
    
    Usage:
        @with_db_session
        def create_user(db: Session, name: str):
            user = User(name=name)
            db.add(user)
            # Auto-commit on success, auto-rollback on exception
            return user
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with get_db_session() as db:
            return func(db, *args, **kwargs)
    return wrapper


def with_db_session_classmethod(func: F) -> F:
    """
    Decorator for class methods that need a database session with automatic transaction management.
    
    Usage:
        @classmethod
        @with_db_session_classmethod
        def create_user(cls, db: Session, name: str):
            user = User(name=name)
            db.add(user)
            # Auto-commit on success, auto-rollback on exception
            return user
    """
    @functools.wraps(func)
    def wrapper(cls, *args, **kwargs):
        with get_db_session() as db:
            return func(cls, db, *args, **kwargs)
    return wrapper


def with_db_session_for_class_instance(func: F) -> F:
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        with get_db_session() as db:
            return func(self, db, *args, **kwargs)
    return wrapper


def with_db_session_manual(func: F) -> F:
    """
    Decorator for functions that need a database session with manual transaction management.
    
    Usage:
        @with_db_session_manual
        def create_user(db: Session, name: str):
            user = User(name=name)
            db.add(user)
            db.commit()  # You must manually commit
            return user
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with get_db_session_manual() as db:
            return func(db, *args, **kwargs)
    return wrapper


def with_db_session_async(func: AsyncF) -> AsyncF:
    """
    Decorator for async functions that need a database session with automatic transaction management.
    
    Usage:
        @with_db_session_async
        async def create_user_async(db: Session, name: str):
            user = User(name=name)
            db.add(user)
            # Auto-commit on success, auto-rollback on exception
            return user
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        with get_db_session() as db:
            return await func(db, *args, **kwargs)
    return wrapper


def with_db_session_manual_async(func: AsyncF) -> AsyncF:
    """
    Decorator for async functions that need a database session with manual transaction management.
    
    Usage:
        @with_db_session_manual_async
        async def create_user_async(db: Session, name: str):
            user = User(name=name)
            db.add(user)
            db.commit()  # You must manually commit
            return user
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        with get_db_session_manual() as db:
            return await func(db, *args, **kwargs)
    return wrapper


class DatabaseManager:
    """Database manager class for advanced operations."""
    
    def __init__(self):
        self.engine = get_engine()
        self.session_factory = get_session_factory()
    
    def health_check(self) -> bool:
        """
        Check database connectivity and health.
        
        Returns:
            bool: True if database is healthy, False otherwise
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                return result.fetchone()[0] == 1
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
    
    def get_connection_info(self) -> dict:
        """
        Get database connection information.
        
        Returns:
            dict: Connection information including pool status
        """
        pool = self.engine.pool
        return {
            "database_url": str(self.engine.url).replace(self.engine.url.password or "", "***"),
            "pool_size": pool.size(),
            "checked_in_connections": pool.checkedin(),
            "checked_out_connections": pool.checkedout(),
            "overflow_connections": pool.overflow(),
            "total_connections": pool.size() + pool.overflow(),
        }
    
    def close_all_connections(self):
        """Close all database connections."""
        self.engine.dispose()
        logger.info("All database connections closed")
    
    def create_tables(self):
        """Create all tables defined in models."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")
    
    def drop_tables(self):
        """Drop all tables. Use with caution!"""
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")


db_manager = DatabaseManager()
