"""
PostgreSQL database connection module.
This module provides backward compatibility and convenience imports.
For new code, use app.core.database directly.
"""

from app.core.database import (
    get_db,
    get_async_db,
    init_database,
    close_database,
    get_database_manager,
    db_manager
)

# Re-export for backward compatibility
__all__ = [
    "get_db",
    "get_async_db", 
    "init_database",
    "close_database",
    "get_database_manager",
    "db_manager"
]
