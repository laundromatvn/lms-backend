from enum import Enum
import uuid
from typing import Optional

from sqlalchemy import (
    Boolean,
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


class FirmwareStatus(str, Enum):
    DRAFT = "DRAFT"
    RELEASED = "RELEASED"
    OUT_OF_DATE = "OUT_OF_DATE"
    DEPRECATED = "DEPRECATED"


class FirmwareVersionType(str, Enum):
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    PATCH = "PATCH"


class Firmware(Base):
    __tablename__ = "firmwares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)

    name = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    status = Column(
        SQLEnum(FirmwareStatus, name="firmware_status", create_type=False),
        nullable=False,
        default=FirmwareStatus.DRAFT,
        index=True
    )
    version_type = Column(
        SQLEnum(FirmwareVersionType, name="firmware_version_type", create_type=False),
        nullable=False,
        default=FirmwareVersionType.PATCH,
        index=True
    )

    object_name = Column(String(255), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    checksum = Column(String(128), nullable=False)
    
    # Relationships
    provisioned_controllers = relationship("Controller", back_populates="provisioned_firmware")

    @validates('version_type')
    def validate_version_type(self, key: str, version_type) -> FirmwareVersionType:
        if not isinstance(version_type, FirmwareVersionType):
            try:
                version_type = FirmwareVersionType(version_type)
            except ValueError:
                raise ValueError(f"Invalid version type: {version_type}. Must be one of {[v.value for v in FirmwareVersionType]}")
        
        return version_type

    @validates('status')
    def validate_status(self, key: str, status) -> FirmwareStatus:
        if not isinstance(status, FirmwareStatus):
            try:
                status = FirmwareStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status: {status}. Must be one of {[s.value for s in FirmwareStatus]}")
        return status
    
    @property
    def is_active(self) -> bool:
        return self.status == FirmwareStatus.RELEASED and self.deleted_at is None
    
    @property
    def is_released(self) -> bool:
        return self.status == FirmwareStatus.RELEASED
    
    @property
    def is_out_of_date(self) -> bool:
        return self.status == FirmwareStatus.OUT_OF_DATE
    
    @property
    def is_deprecated(self) -> bool:
        return self.status == FirmwareStatus.DEPRECATED
    
    @property
    def is_draft(self) -> bool:
        return self.status == FirmwareStatus.DRAFT

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, deleted_by: uuid.UUID) -> None:
        self.deleted_at = func.now()
        self.deleted_by = deleted_by

    def restore(self) -> None:
        self.deleted_at = None
        self.deleted_by = None
        self.status = FirmwareStatus.DRAFT

    def release(self, updated_by: uuid.UUID) -> None:
        self.status = FirmwareStatus.RELEASED
        self.updated_by = updated_by

    def mark_as_out_of_date(self, updated_by: uuid.UUID) -> None:
        self.status = FirmwareStatus.OUT_OF_DATE
        self.updated_by = updated_by

    def deprecate(self, updated_by: uuid.UUID) -> None:
        self.status = FirmwareStatus.DEPRECATED
        self.updated_by = updated_by
        
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "deleted_by": self.deleted_by,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "status": self.status,
            "version_type": self.version_type,
            "object_name": self.object_name,
            "file_size": self.file_size,
            "checksum": self.checksum,
        }

@event.listens_for(Firmware, 'before_update', propagate=True)
def update_timestamp(mapper, connection, target):
    target.updated_at = func.now()
