from datetime import datetime
from uuid import UUID
from typing import Any, Dict, Optional

from pydantic import BaseModel

from app.models.system_task import SystemTaskStatus
from app.enums.system_task_type_enum import SystemTaskTypeEnum


class SystemTaskSerializer(BaseModel):
    """Serializer for SystemTask model."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    expired_at: Optional[datetime] = None
    expires_time: Optional[int] = None
    task_type: Optional[SystemTaskTypeEnum] = None
    status: SystemTaskStatus
    data: Optional[Dict[str, Any]] = None


class CreateSystemTaskRequest(BaseModel):
    """Request schema for creating a system task."""
    task_type: Optional[SystemTaskTypeEnum] = None
    data: Optional[Dict[str, Any]] = None
    expires_time_seconds: Optional[int] = None


class UpdateSystemTaskRequest(BaseModel):
    """Request schema for updating a system task."""
    data: Optional[Dict[str, Any]] = None
    task_type: Optional[SystemTaskTypeEnum] = None


class SystemTaskStatusUpdateRequest(BaseModel):
    """Request schema for updating system task status."""
    status: SystemTaskStatus
    result_data: Optional[Dict[str, Any]] = None
    error_data: Optional[Dict[str, Any]] = None


class SystemTaskExpirationRequest(BaseModel):
    """Request schema for setting task expiration."""
    expires_time_seconds: int


class SystemTaskQueryParams(BaseModel):
    """Query parameters for listing system tasks."""
    task_type: Optional[SystemTaskTypeEnum] = None
    status: Optional[SystemTaskStatus] = None
    limit: int = 100
    offset: int = 0
    include_expired: bool = False


class SystemTaskStatistics(BaseModel):
    """Statistics about system tasks."""
    total_count: int
    active_count: int
    expired_count: int
    status_counts: Dict[str, int]
    task_type: Optional[SystemTaskTypeEnum] = None
