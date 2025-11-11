from enum import Enum
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    func,
    ForeignKey,
    Enum as SQLEnum,
    event,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates, relationship

from app.libs.database import Base


class FirmwareDeploymentStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FirmwareDeployment(Base):
    __tablename__ = "firmware_deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    firmware_id = Column(UUID(as_uuid=True), ForeignKey('firmwares.id'), nullable=False, index=True)
    controller_id = Column(UUID(as_uuid=True), ForeignKey('controllers.id'), nullable=False, index=True)

    status = Column(
        SQLEnum(FirmwareDeploymentStatus, name="firmware_deployment_status", create_type=False),
        nullable=False,
        default=FirmwareDeploymentStatus.NEW,
        index=True
    )

    # Relationships
    firmware = relationship("Firmware", back_populates="deployments")
    controller = relationship("Controller", back_populates="deployments")

    @validates('status')
    def validate_status(self, key: str, status) -> FirmwareDeploymentStatus:
        if not isinstance(status, FirmwareDeploymentStatus):
            try:
                status = FirmwareDeploymentStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status: {status}. Must be one of {[s.value for s in FirmwareDeploymentStatus]}")
        return status

    @property
    def is_new(self) -> bool:
        return self.status == FirmwareDeploymentStatus.NEW

    @property
    def is_in_progress(self) -> bool:
        return self.status == FirmwareDeploymentStatus.IN_PROGRESS

    @property
    def is_completed(self) -> bool:
        return self.status == FirmwareDeploymentStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        return self.status == FirmwareDeploymentStatus.FAILED

    @property
    def is_cancelled(self) -> bool:
        return self.status == FirmwareDeploymentStatus.CANCELLED


@event.listens_for(FirmwareDeployment, 'before_update', propagate=True)
def update_timestamp(mapper, connection, target):
    target.updated_at = func.now()  


