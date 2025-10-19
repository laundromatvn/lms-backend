"""
System Task API endpoints.

This module contains all FastAPI endpoints for system task management including
CRUD operations, status updates, and task retrieval.
"""

from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.libs.database import get_db
from app.models.user import User
from app.models.system_task import SystemTaskStatus
from app.enums.system_task_type_enum import SystemTaskTypeEnum
from app.operations.system_task_operation import SystemTaskOperation
from app.schemas.system_task import (
    SystemTaskSerializer,
    CreateSystemTaskRequest,
    UpdateSystemTaskRequest,
    SystemTaskStatusUpdateRequest,
    SystemTaskExpirationRequest,
    SystemTaskQueryParams,
    SystemTaskStatistics,
)

router = APIRouter()


@router.post("", response_model=SystemTaskSerializer, status_code=201)
async def create_system_task(
    request: CreateSystemTaskRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new system task.
    
    This endpoint creates a new system task with the specified type, data, and optional expiration time.
    The task will be created with status NEW.
    """
    try:
        task = SystemTaskOperation.create(
            task_type=request.task_type,
            data=request.data,
            expires_time_seconds=request.expires_time_seconds
        )
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating system task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{task_id}", response_model=SystemTaskSerializer)
async def get_system_task(
    task_id: UUID = Path(..., description="System task ID"),
    current_user: User = Depends(get_current_user)
):
    """
    Get a system task by ID.
    
    This endpoint retrieves a specific system task by its UUID.
    """
    try:
        task = SystemTaskOperation.get(task_id)
        return task.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting system task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
