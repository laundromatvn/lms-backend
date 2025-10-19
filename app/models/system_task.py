import uuid
from enum import Enum
from typing import Optional, Any, Dict
from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    String,
    func,
    event,
    JSON,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates

from app.libs.database import Base
from app.enums.system_task_type_enum import SystemTaskTypeEnum


class SystemTaskStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class SystemTask(Base):
    __tablename__ = "system_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    expired_at = Column(DateTime(timezone=True), nullable=True, index=True)
    expires_time = Column(Integer, nullable=True)  # Time in seconds until expiration
    
    task_type = Column(String(100), nullable=True, index=True)
    status = Column(
        SQLEnum(SystemTaskStatus, name="system_task_status", create_type=False),
        nullable=False,
        default=SystemTaskStatus.NEW,
        index=True
    )
    data = Column(JSON, nullable=True)  # JSON field to store any data
    
    @validates('status')
    def validate_status(self, key: str, status) -> SystemTaskStatus:
        if not isinstance(status, SystemTaskStatus):
            try:
                status = SystemTaskStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status: {status}. Must be one of {[s.value for s in SystemTaskStatus]}")
        return status
    
    @validates('expires_time')
    def validate_expires_time(self, key: str, expires_time: Optional[int]) -> Optional[int]:
        if expires_time is not None and expires_time <= 0:
            raise ValueError("Expires time must be a positive integer (seconds)")
        return expires_time
    
    @validates('task_type')
    def validate_task_type(self, key: str, task_type) -> Optional[str]:
        if task_type is not None:
            # If it's already a SystemTaskTypeEnum, convert to string
            if isinstance(task_type, SystemTaskTypeEnum):
                return task_type.value
            
            # If it's a string, validate it's a valid enum value
            if isinstance(task_type, str):
                try:
                    SystemTaskTypeEnum(task_type)
                    return task_type
                except ValueError:
                    raise ValueError(f"Invalid task type: {task_type}. Must be one of {[t.value for t in SystemTaskTypeEnum]}")
            
            # If it's neither, try to convert to string and validate
            try:
                enum_value = SystemTaskTypeEnum(str(task_type))
                return enum_value.value
            except ValueError:
                raise ValueError(f"Invalid task type: {task_type}. Must be one of {[t.value for t in SystemTaskTypeEnum]}")
        
        return task_type
    
    def validate_task_data(self) -> None:
        """Validate task data based on task type."""
        if self.task_type is None:
            return
        
        if self.data is None:
            raise ValueError(f"Data is required for task type: {self.task_type}")
        
        if self.task_type == SystemTaskTypeEnum.SIGN_IN.value:
            self._validate_sign_in_data()
        elif self.task_type == SystemTaskTypeEnum.AUTHORIZE_STORE_CONFIGURATION_ACCESS.value:
            self._validate_authorize_store_configuration_access_data()
    
    def _validate_sign_in_data(self) -> None:
        """Validate data for SIGN_IN task type."""
        required_fields = ['phone', 'otp_code']
        for field in required_fields:
            if field not in self.data:
                raise ValueError(f"Field '{field}' is required for SIGN_IN task type")
        
        # Validate phone format
        phone = self.data.get('phone')
        if not phone or not isinstance(phone, str):
            raise ValueError("Phone must be a non-empty string for SIGN_IN task type")
        
        # Validate OTP code
        otp_code = self.data.get('otp_code')
        if not otp_code or not isinstance(otp_code, str):
            raise ValueError("OTP code must be a non-empty string for SIGN_IN task type")
        
        if len(otp_code) != 6 or not otp_code.isdigit():
            raise ValueError("OTP code must be a 6-digit string for SIGN_IN task type")
    
    def _validate_authorize_store_configuration_access_data(self) -> None:
        """Validate data for AUTHORIZE_STORE_CONFIGURATION_ACCESS task type."""
        required_fields = ['user_id', 'store_id', 'permission_type']
        for field in required_fields:
            if field not in self.data:
                raise ValueError(f"Field '{field}' is required for AUTHORIZE_STORE_CONFIGURATION_ACCESS task type")
        
        # Validate user_id
        user_id = self.data.get('user_id')
        if not user_id:
            raise ValueError("User ID is required for AUTHORIZE_STORE_CONFIGURATION_ACCESS task type")
        
        # Validate store_id
        store_id = self.data.get('store_id')
        if not store_id:
            raise ValueError("Store ID is required for AUTHORIZE_STORE_CONFIGURATION_ACCESS task type")
        
        # Validate permission_type
        permission_type = self.data.get('permission_type')
        valid_permissions = ['read', 'write', 'admin']
        if permission_type not in valid_permissions:
            raise ValueError(f"Permission type must be one of {valid_permissions} for AUTHORIZE_STORE_CONFIGURATION_ACCESS task type")
    
    def set_expiration(self, expires_time_seconds: int) -> None:
        """Set the expiration time for this task."""
        if expires_time_seconds <= 0:
            raise ValueError("Expires time must be a positive integer (seconds)")
        
        self.expires_time = expires_time_seconds
        self.expired_at = datetime.now(timezone.utc) + timedelta(seconds=expires_time_seconds)
    
    def set_default_expiration(self) -> None:
        """Set default expiration time of 900 seconds (15 minutes)."""
        self.set_expiration(900)
    
    def is_expired(self) -> bool:
        """Check if the task has expired."""
        if self.expired_at is None:
            return False
        return datetime.now(timezone.utc) > self.expired_at
    
    def is_completed(self) -> bool:
        """Check if the task is in a completed state (success or failed)."""
        return self.status in [SystemTaskStatus.SUCCESS, SystemTaskStatus.FAILED]
    
    def is_active(self) -> bool:
        """Check if the task is active (not completed and not expired)."""
        return not self.is_completed() and not self.is_expired()
    
    def mark_in_progress(self) -> None:
        """Mark the task as in progress."""
        if self.status != SystemTaskStatus.NEW:
            raise ValueError("Only NEW tasks can be marked as in progress")
        self.status = SystemTaskStatus.IN_PROGRESS
    
    def mark_success(self, result_data: Optional[Dict[str, Any]] = None) -> None:
        """Mark the task as successful with optional result data."""
        if self.status not in [SystemTaskStatus.NEW, SystemTaskStatus.IN_PROGRESS]:
            raise ValueError("Only NEW or IN_PROGRESS tasks can be marked as successful")
        
        self.status = SystemTaskStatus.SUCCESS
        if result_data is not None:
            # Merge result data with existing data
            current_data = self.data or {}
            current_data.update(result_data)
            self.data = current_data
    
    def mark_failed(self, error_data: Optional[Dict[str, Any]] = None) -> None:
        """Mark the task as failed with optional error data."""
        if self.status not in [SystemTaskStatus.NEW, SystemTaskStatus.IN_PROGRESS]:
            raise ValueError("Only NEW or IN_PROGRESS tasks can be marked as failed")
        
        self.status = SystemTaskStatus.FAILED
        if error_data is not None:
            # Merge error data with existing data
            current_data = self.data or {}
            current_data.update(error_data)
            self.data = current_data
    
    def update_data(self, new_data: Dict[str, Any]) -> None:
        """Update the task data by merging with existing data."""
        current_data = self.data or {}
        current_data.update(new_data)
        self.data = current_data
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get a specific value from the task data."""
        if self.data is None:
            return default
        return self.data.get(key, default)
    
    def to_dict(self) -> dict:
        """Convert the task to a dictionary representation."""
        try:
            is_expired = self.is_expired()
            is_completed = self.is_completed()
            is_active = self.is_active()
        except Exception:
            # Fallback values if methods fail
            is_expired = False
            is_completed = False
            is_active = True
        
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expired_at': self.expired_at.isoformat() if self.expired_at else None,
            'expires_time': self.expires_time,
            'task_type': self.task_type,
            'status': self.status.value if hasattr(self.status, 'value') else str(self.status),
            'data': self.data,
            'is_expired': is_expired,
            'is_completed': is_completed,
            'is_active': is_active,
        }
    
    def __repr__(self) -> str:
        return f"<SystemTask(id={self.id}, task_type={self.task_type}, status={self.status.value})>"


@event.listens_for(SystemTask, 'before_insert', propagate=True)
def set_default_expiration_on_insert(mapper, connection, target):
    """Set default expiration time and validate system task data on insert."""
    # Set default expiration if not already set
    if target.expires_time is None:
        target.set_default_expiration()
    
    target.validate_task_data()
    target.updated_at = func.now()


@event.listens_for(SystemTask, 'before_update', propagate=True)
def validate_system_task_on_update(mapper, connection, target):
    """Validate system task data and update timestamp on update."""
    target.validate_task_data()
    target.updated_at = func.now()
