import uuid
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    func,
    event,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates, relationship

from app.libs.database import Base


class TenantStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)

    status = Column(
        SQLEnum(TenantStatus, name="tenant_status", create_type=False),
        nullable=False,
        default=TenantStatus.ACTIVE,
        index=True
    )
    
    name = Column(String(255), nullable=False, index=True)
    contact_email = Column(String(255), nullable=False, index=True)
    contact_phone_number = Column(String(20), nullable=False, index=True)
    contact_full_name = Column(String(255), nullable=False)
    contact_address = Column(String(500), nullable=False)

    # Relationships
    payments = relationship("Payment", back_populates="tenant")

    @validates('status')
    def validate_status(self, key: str, status) -> TenantStatus:
        if not isinstance(status, TenantStatus):
            try:
                status = TenantStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status: {status}. Must be one of {[s.value for s in TenantStatus]}")
        return status
    
    @validates('contact_email')
    def validate_contact_email(self, key: str, email: str) -> str:
        if not email:
            raise ValueError("Contact email is required")
        
        email = email.strip().lower()
        if not email or '@' not in email:
            raise ValueError("Invalid email format")
        
        return email
    
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
    
    @validates('contact_full_name')
    def validate_contact_full_name(self, key: str, name: str) -> str:
        if not name:
            raise ValueError("Contact full name is required")
        
        name = name.strip()
        if not name:
            raise ValueError("Contact full name cannot be empty")
        
        if len(name) < 2:
            raise ValueError("Contact full name must be at least 2 characters long")
        
        return name
    
    @validates('contact_address')
    def validate_contact_address(self, key: str, address: str) -> str:
        if not address:
            raise ValueError("Contact address is required")
        
        address = address.strip()
        if not address:
            raise ValueError("Contact address cannot be empty")
        
        if len(address) < 10:
            raise ValueError("Contact address must be at least 10 characters long")
        
        return address
    
    def is_active(self) -> bool:
        return self.status == TenantStatus.ACTIVE and self.deleted_at is None
    
    def soft_delete(self, deleted_by: Optional[uuid.UUID] = None) -> None:
        self.deleted_at = func.now()
        self.deleted_by = deleted_by
        self.status = TenantStatus.INACTIVE
    
    def restore(self) -> None:
        self.deleted_at = None
        self.deleted_by = None
        if self.status == TenantStatus.INACTIVE:
            self.status = TenantStatus.ACTIVE
    
    def activate(self, updated_by: Optional[uuid.UUID] = None) -> None:
        if self.status == TenantStatus.INACTIVE:
            self.status = TenantStatus.ACTIVE
            self.updated_by = updated_by
        else:
            raise ValueError("Only inactive tenants can be activated")
    
    def deactivate(self, updated_by: Optional[uuid.UUID] = None) -> None:
        if self.status == TenantStatus.ACTIVE:
            self.status = TenantStatus.INACTIVE
            self.updated_by = updated_by
        else:
            raise ValueError("Only active tenants can be deactivated")
    
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
            'contact_email': self.contact_email,
            'contact_phone_number': self.contact_phone_number,
            'contact_full_name': self.contact_full_name,
            'contact_address': self.contact_address,
        }


@event.listens_for(Tenant, 'before_update', propagate=True)
def update_timestamp(mapper, connection, target):
    target.updated_at = func.now()
