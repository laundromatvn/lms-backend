from enum import Enum
import uuid
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Float,
    func,
    event,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates, relationship

from app.libs.database import Base


class StoreStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Store(Base):
    __tablename__ = "stores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)

    status = Column(
        SQLEnum(StoreStatus, name="store_status", create_type=False),
        nullable=False,
        default=StoreStatus.ACTIVE,
        index=True
    )
    name = Column(String(255), nullable=False, index=True)
    address = Column(String(500), nullable=False)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    contact_phone_number = Column(String(20), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)

    # Payment information
    payment_methods = Column(JSON, nullable=True, default=list)

    # Relationships
    orders = relationship("Order", back_populates="store")
    payments = relationship("Payment", back_populates="store")
    controllers = relationship("Controller", back_populates="store")
    datapoints = relationship("Datapoint", back_populates="store")

    @validates('status')
    def validate_status(self, key: str, status) -> StoreStatus:
        if not isinstance(status, StoreStatus):
            try:
                status = StoreStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status: {status}. Must be one of {[s.value for s in StoreStatus]}")
        return status

    @validates('tenant_id')
    def validate_tenant_id(self, key: str, tenant_id) -> uuid.UUID:
        if not tenant_id:
            raise ValueError("Tenant ID is required")
        
        if not isinstance(tenant_id, uuid.UUID):
            try:
                tenant_id = uuid.UUID(str(tenant_id))
            except (ValueError, TypeError):
                raise ValueError("Invalid tenant ID format")
        
        return tenant_id

    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        if not name:
            raise ValueError("Store name is required")
        
        name = name.strip()
        if not name:
            raise ValueError("Store name cannot be empty")
        
        if len(name) < 2:
            raise ValueError("Store name must be at least 2 characters long")
        
        if len(name) > 255:
            raise ValueError("Store name cannot exceed 255 characters")
        
        return name
    
    @validates('address')
    def validate_address(self, key: str, address: str) -> str:
        if not address:
            raise ValueError("Store address is required")
        
        address = address.strip()
        if not address:
            raise ValueError("Store address cannot be empty")
        
        if len(address) < 10:
            raise ValueError("Store address must be at least 10 characters long")
        
        if len(address) > 500:
            raise ValueError("Store address cannot exceed 500 characters")
        
        return address
    
    @validates('contact_phone_number')
    def validate_contact_phone_number(self, key: str, phone: str) -> str:
        if not phone:
            raise ValueError("Contact phone number is required")
        
        phone = phone.strip()
        if not phone:
            raise ValueError("Phone number cannot be empty")
        
        import re
        if not re.match(r'^\+?[\d\s\-\(\)]{10,20}$', phone):
            raise ValueError("Invalid phone number format")
        
        return phone
    
    @validates('latitude')
    def validate_latitude(self, key: str, latitude: Optional[float]) -> Optional[float]:
        if latitude is not None:
            if not -90 <= latitude <= 90:
                raise ValueError("Latitude must be between -90 and 90 degrees")
        return latitude

    @validates('longitude')
    def validate_longitude(self, key: str, longitude: Optional[float]) -> Optional[float]:
        if longitude is not None:
            if not -180 <= longitude <= 180:
                raise ValueError("Longitude must be between -180 and 180 degrees")
        return longitude
    
    @validates('payment_methods')
    def validate_payment_methods(self, key: str, payment_methods: Optional[list]) -> Optional[list]:
        if payment_methods is None:
            return []

        for method in payment_methods:
            if not isinstance(method, dict):
                raise ValueError("Each payment method must be a dictionary")
            
            payment_method = method.get('payment_method')
            payment_provider = method.get('payment_provider')
            details = method.get('details')
            
            if not payment_method:
                raise ValueError("Each payment method must have a 'payment_method' field")
            
            if not details:
                raise ValueError("Each payment method must have a 'details' field")
            
            if not isinstance(details, dict):
                raise ValueError("Payment method details must be a dictionary")
            
            # Validate QR payment method structure
            if payment_method == 'QR':
                required_fields = [
                    'bank_code',
                    'bank_name',
                    'bank_account_number',
                    'bank_account_name',
                ]
                for field in required_fields:
                    if field not in details:
                        raise ValueError(f"QR payment method must have '{field}' in details")
                    
                    if not isinstance(details[field], str):
                        raise ValueError(f"QR payment method '{field}' must be a string")
            
            elif payment_method == 'CARD' and payment_provider == 'VNPAY':
                required_fields = [
                    'merchant_code',
                    'terminal_code',
                    'init_secret_key',
                    'query_secret_key',
                    'ipnv3_secret_key',
                ]
                for field in required_fields:
                    if field not in details:
                        raise ValueError(f"CARD VNPAY payment method must have '{field}' in details")
            
            else:
                raise ValueError(f"Invalid payment method: {payment_method}")

        return payment_methods
    
    @property
    def is_active(self) -> bool:
        return self.status == StoreStatus.ACTIVE and self.deleted_at is None
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    def soft_delete(self, deleted_by: Optional[uuid.UUID] = None) -> None:
        self.deleted_at = func.now()
        self.deleted_by = deleted_by
        self.status = StoreStatus.INACTIVE

    def restore(self) -> None:
        self.deleted_at = None
    
    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'deleted_by': str(self.deleted_by) if self.deleted_by else None,
            'status': self.status.value,
            'name': self.name,
            'address': self.address,
            'longitude': self.longitude,
            'latitude': self.latitude,
            'contact_phone_number': self.contact_phone_number,
            'tenant_id': str(self.tenant_id),
            'payment_methods': self.payment_methods or [],
        }


@event.listens_for(Store, 'before_update', propagate=True)
def update_timestamp(mapper, connection, target):
    target.updated_at = func.now()
