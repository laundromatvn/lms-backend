from enum import Enum
import uuid
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Integer,
    func,
    event,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates, relationship

from app.libs.database import Base


class ControllerStatus(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Controller(Base):
    __tablename__ = "controllers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(
        SQLEnum(ControllerStatus, name="controller_status", create_type=False),
        nullable=False,
        default=ControllerStatus.NEW,
        index=True
    )
    device_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=True, index=True)
    total_relays = Column(Integer, nullable=False, default=0)
    provisioned_firmware_id = Column(UUID(as_uuid=True), ForeignKey('firmwares.id'), nullable=True, index=True)

    # Relationships
    provisioned_firmware = relationship("Firmware", back_populates="provisioned_controllers")
    machines = relationship("Machine", back_populates="controller")
    store = relationship("Store", back_populates="controllers")
    datapoints = relationship("Datapoint", back_populates="controller")

    @validates('status')
    def validate_status(self, key: str, status) -> ControllerStatus:
        if not isinstance(status, ControllerStatus):
            try:
                status = ControllerStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status: {status}. Must be one of {[s.value for s in ControllerStatus]}")
        return status

    @validates('device_id')
    def validate_device_id(self, key: str, device_id: str) -> str:
        if not device_id:
            raise ValueError("Device ID is required")
        
        device_id = device_id.strip()
        if not device_id:
            raise ValueError("Device ID cannot be empty")
        
        if len(device_id) < 3:
            raise ValueError("Device ID must be at least 3 characters long")
        
        if len(device_id) > 255:
            raise ValueError("Device ID cannot exceed 255 characters")
        
        # Basic validation for device ID format (alphanumeric with hyphens/underscores)
        import re
        if not re.match(r'^[a-zA-Z0-9\-_]+$', device_id):
            raise ValueError("Device ID can only contain alphanumeric characters, hyphens, and underscores")
        
        return device_id

    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        if name is None:
            return None
        
        name = name.strip()
        if not name:
            return None
        
        if len(name) > 255:
            raise ValueError("Controller name cannot exceed 255 characters")
        
        return name

    @validates('store_id')
    def validate_store_id(self, key: str, store_id) -> Optional[uuid.UUID]:
        if store_id is None:
            return None
        
        if not isinstance(store_id, uuid.UUID):
            try:
                store_id = uuid.UUID(str(store_id))
            except (ValueError, TypeError):
                raise ValueError("Invalid store ID format")
        
        return store_id

    @validates('total_relays')
    def validate_total_relays(self, key: str, total_relays: int) -> int:
        if not isinstance(total_relays, int):
            try:
                total_relays = int(total_relays)
            except (ValueError, TypeError):
                raise ValueError("Total relays must be an integer")
        
        if total_relays < 0:
            raise ValueError("Total relays must be at least 0")
        
        if total_relays > 50:  # Reasonable limit
            raise ValueError("Total relays cannot exceed 50")
        
        return total_relays

    @property
    def is_active(self) -> bool:
        return self.status == ControllerStatus.ACTIVE and self.deleted_at is None
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    def soft_delete(self) -> None:
        self.deleted_at = func.now()
        self.status = ControllerStatus.INACTIVE

    def restore(self) -> None:
        self.deleted_at = None
        if self.status == ControllerStatus.INACTIVE:
            self.status = ControllerStatus.NEW

    def activate(self) -> None:
        if self.status in [ControllerStatus.NEW, ControllerStatus.INACTIVE]:
            self.status = ControllerStatus.ACTIVE
        else:
            raise ValueError("Only new or inactive controllers can be activated")
    
    def deactivate(self) -> None:
        if self.status == ControllerStatus.ACTIVE:
            self.status = ControllerStatus.INACTIVE
        else:
            raise ValueError("Only active controllers can be deactivated")

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'status': self.status.value,
            'device_id': self.device_id,
            'name': self.name,
            'store_id': str(self.store_id) if self.store_id else None,
            'total_relays': self.total_relays,
        }


@event.listens_for(Controller, 'before_update', propagate=True)
def update_timestamp(mapper, connection, target):
    target.updated_at = func.now()
