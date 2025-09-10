"""
Database module for centralized database management.
Provides SQLAlchemy integration with FastAPI dependency injection.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from fastapi import Depends
import subprocess
import os

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

    def run_migrations(self, auto_migrate: bool = True) -> bool:
        """
        Run database migrations using Alembic.
        
        Args:
            auto_migrate: If True, automatically apply migrations. If False, only check status.
            
        Returns:
            bool: True if migrations were successful or no migrations needed
        """
        try:
            # Get the project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            # Change to project root directory
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                if auto_migrate:
                    logger.info("Running database migrations...")
                    result = subprocess.run(
                        ["alembic", "upgrade", "head"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    logger.info("Database migrations completed successfully")
                    if result.stdout:
                        logger.info("Migration output", output=result.stdout)
                    return True
                else:
                    # Just check migration status
                    result = subprocess.run(
                        ["alembic", "current"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    logger.info("Migration status", status=result.stdout.strip())
                    return True
                    
            except subprocess.CalledProcessError as e:
                logger.error(
                    "Migration failed",
                    error=e.stderr,
                    returncode=e.returncode
                )
                return False
            finally:
                # Restore original working directory
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error("Failed to run migrations", error=str(e))
            return False

    def downgrade_migrations(self, revision: str = "base") -> bool:
        """
        Downgrade database migrations using Alembic.
        
        Args:
            revision: Target revision to downgrade to (default: "base" for complete rollback)
            
        Returns:
            bool: True if downgrade was successful
        """
        try:
            # Get the project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            # Change to project root directory
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                logger.info("Downgrading database migrations", target_revision=revision)
                result = subprocess.run(
                    ["alembic", "downgrade", revision],
                    capture_output=True,
                    text=True,
                    check=True
                )
                logger.info("Database downgrade completed successfully")
                if result.stdout:
                    logger.info("Downgrade output", output=result.stdout)
                return True
                    
            except subprocess.CalledProcessError as e:
                logger.error(
                    "Downgrade failed",
                    error=e.stderr,
                    returncode=e.returncode
                )
                return False
            finally:
                # Restore original working directory
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error("Failed to downgrade migrations", error=str(e))
            return False

    def create_migration(self, message: str) -> bool:
        """
        Create a new migration file.
        
        Args:
            message: Description of the migration
            
        Returns:
            bool: True if migration file was created successfully
        """
        try:
            # Get the project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            # Change to project root directory
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                logger.info("Creating new migration", message=message)
                result = subprocess.run(
                    ["alembic", "revision", "--autogenerate", "-m", message],
                    capture_output=True,
                    text=True,
                    check=True
                )
                logger.info("Migration file created successfully")
                if result.stdout:
                    logger.info("Migration creation output", output=result.stdout)
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(
                    "Failed to create migration",
                    error=e.stderr,
                    returncode=e.returncode
                )
                return False
            finally:
                # Restore original working directory
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error("Failed to create migration", error=str(e))
            return False

    def get_migration_status(self) -> dict:
        """
        Get current migration status.
        
        Returns:
            dict: Migration status information
        """
        try:
            # Get the project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            # Change to project root directory
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            try:
                # Get current revision
                current_result = subprocess.run(
                    ["alembic", "current"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Get heads
                heads_result = subprocess.run(
                    ["alembic", "heads"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Get history
                history_result = subprocess.run(
                    ["alembic", "history", "--verbose"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                return {
                    "current": current_result.stdout.strip(),
                    "heads": heads_result.stdout.strip(),
                    "history": history_result.stdout.strip(),
                    "status": "success"
                }
                
            except subprocess.CalledProcessError as e:
                return {
                    "error": e.stderr,
                    "status": "error"
                }
            finally:
                # Restore original working directory
                os.chdir(original_cwd)
                
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
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


def migrate(auto_migrate: bool = True) -> bool:
    """
    Run database migrations.
    
    Args:
        auto_migrate: If True, automatically apply migrations. If False, only check status.
        
    Returns:
        bool: True if migrations were successful
    """
    return db_manager.run_migrations(auto_migrate=auto_migrate)


def create_migration(message: str) -> bool:
    """
    Create a new migration file.
    
    Args:
        message: Description of the migration
        
    Returns:
        bool: True if migration file was created successfully
    """
    return db_manager.create_migration(message)


def get_migration_status() -> dict:
    """
    Get current migration status.
    
    Returns:
        dict: Migration status information
    """
    return db_manager.get_migration_status()


def downgrade(revision: str = "base") -> bool:
    """
    Downgrade database migrations.
    
    Args:
        revision: Target revision to downgrade to (default: "base" for complete rollback)
        
    Returns:
        bool: True if downgrade was successful
    """
    return db_manager.downgrade_migrations(revision=revision)
