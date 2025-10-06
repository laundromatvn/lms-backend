from enum import Enum
import uuid
from typing import Optional, Dict, Any
import json

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Integer,
    Numeric,
    JSON,
    func,
    event,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates, relationship

from app.libs.database import Base


class MachineType(str, Enum):
    WASHER = "WASHER"
    DRYER = "DRYER"


class MachineStatus(str, Enum):
    PENDING_SETUP = "PENDING_SETUP"
    IDLE = "IDLE"
    STARTING = "STARTING"
    BUSY = "BUSY"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class Machine(Base):
    __tablename__ = "machines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    controller_id = Column(UUID(as_uuid=True), ForeignKey('controllers.id'), nullable=False, index=True)
    relay_no = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=True, index=True, unique=True)
    machine_type = Column(
        SQLEnum(MachineType, name="machine_type", create_type=False),
        nullable=False,
        index=True
    )
    details = Column(JSON, nullable=True, default=dict)
    base_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    status = Column(
        SQLEnum(MachineStatus, name="machine_status", create_type=False),
        nullable=False,
        default=MachineStatus.PENDING_SETUP,
        index=True
    )
    pulse_duration = Column(Integer, nullable=False, default=1000)
    coin_value = Column(Integer, nullable=False, default=10)
    add_ons_options = Column(JSON, nullable=True, default=list)

    # Relationships
    controller = relationship("Controller", back_populates="machines")
    order_details = relationship("OrderDetail", back_populates="machine")

    @validates('controller_id')
    def validate_controller_id(self, key: str, controller_id) -> uuid.UUID:
        if not isinstance(controller_id, uuid.UUID):
            try:
                controller_id = uuid.UUID(str(controller_id))
            except (ValueError, TypeError):
                raise ValueError("Invalid controller ID format")
        
        return controller_id

    @validates('relay_no')
    def validate_relay_no(self, key: str, relay_no: int) -> int:
        if not isinstance(relay_no, int):
            try:
                relay_no = int(relay_no)
            except (ValueError, TypeError):
                raise ValueError("Relay number must be an integer")
        
        if relay_no < 1:
            raise ValueError("Relay number must be at least 1")
        
        return relay_no

    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        if name is None:
            return None
        
        name = name.strip()
        if not name:
            return None
        
        if len(name) > 255:
            raise ValueError("Machine name cannot exceed 255 characters")
        
        return name

    @validates('machine_type')
    def validate_machine_type(self, key: str, machine_type) -> MachineType:
        if not isinstance(machine_type, MachineType):
            try:
                machine_type = MachineType(machine_type)
            except ValueError:
                raise ValueError(f"Invalid machine type: {machine_type}. Must be one of {[t.value for t in MachineType]}")
        return machine_type

    @validates('details')
    def validate_details(self, key: str, details) -> Optional[Dict[str, Any]]:
        if details is None:
            return None
        
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except json.JSONDecodeError:
                raise ValueError("Details must be valid JSON")
        
        if not isinstance(details, dict):
            raise ValueError("Details must be a dictionary")
        
        return details

    @validates('base_price')
    def validate_base_price(self, key: str, base_price) -> float:
        if not isinstance(base_price, (int, float)):
            try:
                base_price = float(base_price)
            except (ValueError, TypeError):
                raise ValueError("Base price must be a number")
        
        if base_price < 0:
            raise ValueError("Base price cannot be negative")
        
        return base_price

    @validates('status')
    def validate_status(self, key: str, status) -> MachineStatus:
        if not isinstance(status, MachineStatus):
            try:
                status = MachineStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status: {status}. Must be one of {[s.value for s in MachineStatus]}")
        return status

    @property
    def is_active(self) -> bool:
        return self.status != MachineStatus.OUT_OF_SERVICE and self.deleted_at is None
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    @property
    def is_available(self) -> bool:
        return self.status == MachineStatus.IDLE and self.deleted_at is None
    
    @property
    def is_ready_for_use(self) -> bool:
        """Check if machine is configured and ready for customer use"""
        return self.status in [MachineStatus.IDLE, MachineStatus.BUSY] and self.deleted_at is None
    
    @property
    def needs_setup(self) -> bool:
        """Check if machine needs initial setup"""
        return self.status == MachineStatus.PENDING_SETUP and self.deleted_at is None
    
    def soft_delete(self) -> None:
        self.deleted_at = func.now()
        self.status = MachineStatus.OUT_OF_SERVICE

    def restore(self) -> None:
        self.deleted_at = None
        self.status = MachineStatus.IDLE

    def activate(self) -> None:
        self.status = MachineStatus.IDLE
        
    def out_of_service(self) -> None:
        self.status = MachineStatus.OUT_OF_SERVICE

    def start(self) -> None:
        if self.status == MachineStatus.IDLE:
            self.status = MachineStatus.STARTING
        else:
            raise ValueError("Only idle machines can start operations")
        
    def mark_as_in_progress(self) -> None:
        if self.status == MachineStatus.STARTING:
            self.status = MachineStatus.BUSY
        else:
            raise ValueError("Only starting machines can be in progress")
    
    def finish_operation(self) -> None:
        if self.status == MachineStatus.BUSY:
            self.status = MachineStatus.IDLE
        else:
            raise ValueError("Only busy machines can finish operations")

    def set_out_of_service(self) -> None:
        self.status = MachineStatus.OUT_OF_SERVICE

    def mark_as_ready(self) -> None:
        """Mark machine as ready for use after setup is complete"""
        if self.status == MachineStatus.PENDING_SETUP:
            self.status = MachineStatus.IDLE
        else:
            raise ValueError("Only machines with PENDING_SETUP status can be marked as ready")

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'controller_id': str(self.controller_id),
            'relay_no': self.relay_no,
            'name': self.name,
            'machine_type': self.machine_type.value,
            'details': self.details,
            'base_price': float(self.base_price) if self.base_price else 0.0,
            'status': self.status.value,
            'pulse_duration': self.pulse_duration,
            'coin_value': self.coin_value,
            'add_ons_options': self.add_ons_options,
        }


@event.listens_for(Machine, 'before_update', propagate=True)
def update_timestamp(mapper, connection, target):
    target.updated_at = func.now()
