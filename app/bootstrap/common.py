from collections.abc import Callable
import time
import os

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import logger
from app.libs.database import db_manager
from app.libs.cache import cache_manager


def bootstrap_services(
    app: FastAPI = None,
    custom_callback: Callable = None,
):
    logger.info("starting", app=settings.APP_NAME)
    init_timezone_and_logging()
    
    # Initialize database
    init_database()
    
    # Initialize Redis cache
    init_redis()

    if custom_callback:
        custom_callback(app)


def shutdown_services(
    app: FastAPI = None,
    custom_callback: Callable = None,
):
    logger.info("stopped", app=settings.APP_NAME)
    
    # Close database connections
    close_database()
    
    # Close Redis connections
    close_redis()

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


def init_redis():
    """Initialize Redis cache connection."""
    try:
        # Test Redis connection
        if not cache_manager.is_connected():
            logger.warning("Redis cache is not available - application will continue without caching")
            return
        
        logger.info("Redis cache connection established successfully")
        
    except Exception as e:
        logger.warning("Failed to initialize Redis cache - application will continue without caching", error=str(e))


def close_redis():
    """Close Redis cache connections."""
    try:
        if cache_manager.redis_client:
            cache_manager.redis_client.close()
            logger.info("Redis cache connections closed")
    except Exception as e:
        logger.error("Failed to close Redis cache connections", error=str(e))
