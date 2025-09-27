from collections.abc import Callable
import time
import os

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import logger
from app.libs.database import db_manager


def bootstrap_services(
    app: FastAPI = None,
    custom_callback: Callable = None,
):
    logger.info("starting", app=settings.APP_NAME)
    init_timezone_and_logging()
    
    # Initialize database
    init_database()

    if custom_callback:
        custom_callback(app)


def shutdown_services(
    app: FastAPI = None,
    custom_callback: Callable = None,
):
    logger.info("stopped", app=settings.APP_NAME)
    
    # Close database connections
    close_database()

    if custom_callback:
        custom_callback(app)


def init_timezone_and_logging():
    os.environ["TZ"] = settings.TIMEZONE_NAME
    try:
        time.tzset()
    except AttributeError:
        pass


def init_database():
    """Initialize the database connection and create tables if needed."""
    try:
        # Test connection
        if not db_manager.health_check():
            raise Exception("Database health check failed")
        
        logger.info("Database connection established successfully")
        
        # Create tables if auto-migrate is enabled
        if settings.AUTO_MIGRATE:
            db_manager.create_tables()
            logger.info("Database tables created (auto-migrate enabled)")
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


def close_database():
    """Close all database connections."""
    db_manager.close_all_connections()
