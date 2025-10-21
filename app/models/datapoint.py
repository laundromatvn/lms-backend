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


class DatapointValueType(str, Enum):
    MACHINE_STATE = "MACHINE_STATE"


class Datapoint(Base):
    __tablename__ = "datapoints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Foreign key relationships
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=True, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=True, index=True)
    controller_id = Column(UUID(as_uuid=True), ForeignKey('controllers.id'), nullable=False, index=True)
    machine_id = Column(UUID(as_uuid=True), ForeignKey('machines.id'), nullable=True, index=True)
    
    # Data fields
    relay_no = Column(Integer, nullable=False, index=True)
    value = Column(String(255), nullable=False)
    value_type = Column(
        SQLEnum(DatapointValueType, name="datapoint_value_type", create_type=False),
        nullable=False,
        index=True
    )
    
    # Relationships
    tenant = relationship("Tenant", back_populates="datapoints")
    store = relationship("Store", back_populates="datapoints")
    controller = relationship("Controller", back_populates="datapoints")
    machine = relationship("Machine", back_populates="datapoints")
    
    @validates('tenant_id')
    def validate_tenant_id(self, key: str, tenant_id) -> Optional[uuid.UUID]:
        if tenant_id is None:
            return None
        
        if not isinstance(tenant_id, uuid.UUID):
            try:
                tenant_id = uuid.UUID(str(tenant_id))
            except (ValueError, TypeError):
                raise ValueError("Invalid tenant ID format")
        
        return tenant_id
    
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
    
    @validates('controller_id')
    def validate_controller_id(self, key: str, controller_id) -> uuid.UUID:
        if not controller_id:
            raise ValueError("Controller ID is required")
        
        if not isinstance(controller_id, uuid.UUID):
            try:
                controller_id = uuid.UUID(str(controller_id))
            except (ValueError, TypeError):
                raise ValueError("Invalid controller ID format")
        
        return controller_id
    
    @validates('machine_id')
    def validate_machine_id(self, key: str, machine_id) -> Optional[uuid.UUID]:
        if machine_id is None:
            return None
        
        if not isinstance(machine_id, uuid.UUID):
            try:
                machine_id = uuid.UUID(str(machine_id))
            except (ValueError, TypeError):
                raise ValueError("Invalid machine ID format")
        
        return machine_id
    
    @validates('relay_no')
    def validate_relay_no(self, key: str, relay_no: int) -> int:
        if not isinstance(relay_no, int):
            try:
                relay_no = int(relay_no)
            except (ValueError, TypeError):
                raise ValueError("Relay number must be an integer")
        
        if relay_no < 1:
            raise ValueError("Relay number must be at least 1")
        
        if relay_no > 50:  # Reasonable limit
            raise ValueError("Relay number cannot exceed 50")
        
        return relay_no
    
    @validates('value')
    def validate_value(self, key: str, value: str) -> str:
        if not value:
            raise ValueError("Value is required")
        
        value = str(value).strip()
        if not value:
            raise ValueError("Value cannot be empty")
        
        if len(value) > 255:
            raise ValueError("Value cannot exceed 255 characters")
        
        return value
    
    @validates('value_type')
    def validate_value_type(self, key: str, value_type) -> DatapointValueType:
        if not isinstance(value_type, DatapointValueType):
            try:
                value_type = DatapointValueType(value_type)
            except ValueError:
                raise ValueError(f"Invalid value type: {value_type}. Must be one of {[t.value for t in DatapointValueType]}")
        return value_type
    
    @property
    def is_controller_data(self) -> bool:
        return self.machine_id is None
    
    @property
    def is_machine_data(self) -> bool:
        return self.machine_id is not None
    
    @property
    def is_tenant_data(self) -> bool:
        return self.tenant_id is not None
    
    @property
    def is_store_data(self) -> bool:
        return self.store_id is not None
    
    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'tenant_id': str(self.tenant_id) if self.tenant_id else None,
            'store_id': str(self.store_id) if self.store_id else None,
            'controller_id': str(self.controller_id),
            'machine_id': str(self.machine_id) if self.machine_id else None,
            'relay_no': self.relay_no,
            'value': self.value,
            'value_type': self.value_type.value,
        }


@event.listens_for(Datapoint, 'before_update', propagate=True)
def update_timestamp(mapper, connection, target):
    target.updated_at = func.now()
