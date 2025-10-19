"""
System Task business logic operations.

This module contains all business logic for system task management including
creation, updates, status management, and expiration handling.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.libs.database import with_db_session_classmethod
from app.models.system_task import SystemTask, SystemTaskStatus
from app.enums.system_task_type_enum import SystemTaskTypeEnum


class SystemTaskOperation:
    """Business logic operations for system task management."""

    @classmethod
    @with_db_session_classmethod
    def create(
        cls,
        db: Session,
        task_type: Optional[SystemTaskTypeEnum] = None,
        data: Optional[Dict[str, Any]] = None,
        expires_time_seconds: Optional[int] = None,
    ) -> SystemTask:
        """
        Create a new system task.

        Args:
            task_type: Type of the task (SystemTaskTypeEnum)
            data: Initial data for the task (optional)
            expires_time_seconds: Time in seconds until task expires (optional)

        Returns:
            Created SystemTask instance
        """
        task = SystemTask(
            task_type=task_type,
            data=data,
        )
        
        if expires_time_seconds:
            task.set_expiration(expires_time_seconds)
        # Note: Default expiration (900s) will be set automatically by the event listener
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        return task

    @classmethod
    @with_db_session_classmethod
    def get(cls, db: Session, task_id: UUID) -> SystemTask: 
        """
        Get system task by ID.
        """
        return db.query(SystemTask).get(task_id)
