import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    String,
    func,
    event,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates

from app.libs.database import Base
from app.utils.security.hash import get_password_hash, verify_password


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    TENANT_STAFF = "TENANT_STAFF"
    CUSTOMER = "CUSTOMER"


class UserStatus(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"


class User(Base):    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    role = Column(
        SQLEnum(UserRole, name="user_roles", create_type=False),
        nullable=False,
        index=True
    )
    status = Column(
        SQLEnum(UserStatus, name="userstatus", create_type=False),
        nullable=False,
        default=UserStatus.NEW,
        index=True
    )
    
    phone = Column(String(20), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password = Column(String(255), nullable=False)
    
    is_verified = Column(Boolean, nullable=False, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    @validates('role')
    def validate_role(self, key: str, role) -> UserRole:
        if not isinstance(role, UserRole):
            try:
                role = UserRole(role)
            except ValueError:
                raise ValueError(f"Invalid role: {role}. Must be one of {[r.value for r in UserRole]}")
        return role

    @validates('status')
    def validate_status(self, key: str, status) -> UserStatus:
        if not isinstance(status, UserStatus):
            try:
                status = UserStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status: {status}. Must be one of {[s.value for s in UserStatus]}")
        return status
    
    @validates('email')
    def validate_email(self, key: str, email: Optional[str]) -> Optional[str]:
        if email is not None:
            email = email.strip().lower()
            if not email or '@' not in email:
                raise ValueError("Invalid email format")
            
            if self.role in [UserRole.ADMIN, UserRole.TENANT_ADMIN, UserRole.TENANT_STAFF] and not email:
                raise ValueError(f"Email is required for role: {self.role.value}")
        
        return email
    
    @validates('phone')
    def validate_phone(self, key: str, phone: Optional[str]) -> Optional[str]:
        if phone is not None:
            phone = phone.strip()
            if not phone:
                raise ValueError("Phone number cannot be empty")
            
            import re
            if not re.match(r'^\+?[\d\s\-\(\)]{10,20}$', phone):
                raise ValueError("Invalid phone number format")
            
            if self.role == UserRole.CUSTOMER and not phone:
                raise ValueError("Phone is required for customer role")
        
        return phone
    
    def validate_username_requirements(self) -> None:
        if self.role == UserRole.CUSTOMER:
            if not self.phone:
                raise ValueError("Phone is required as username for customer role")
        elif self.role in [UserRole.ADMIN, UserRole.TENANT_ADMIN, UserRole.TENANT_STAFF]:
            if not self.email:
                raise ValueError("Email is required as username for admin/tenant roles")
    
    def set_password(self, password: str) -> None:
        if not password:
            raise ValueError("Password cannot be empty")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        self.password = get_password_hash(password)
    
    def verify_password(self, password: str) -> bool:
        return verify_password(password, self.password)
    
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE and self.deleted_at is None
    
    def is_verified_user(self) -> bool:
        return self.is_verified and self.verified_at is not None
    
    def soft_delete(self) -> None:
        self.deleted_at = func.now()
        self.status = UserStatus.INACTIVE
    
    def restore(self) -> None:
        self.deleted_at = None
        if self.status == UserStatus.INACTIVE:
            self.status = UserStatus.NEW
    
    def verify(self) -> None:
        self.is_verified = True
        self.verified_at = func.now()
    
    def activate(self) -> None:
        if self.status == UserStatus.WAITING_FOR_APPROVAL:
            self.status = UserStatus.ACTIVE
        else:
            raise ValueError("Only users waiting for approval can be activated")
    
    def deactivate(self) -> None:
        if self.status == UserStatus.ACTIVE:
            self.status = UserStatus.INACTIVE
        else:
            raise ValueError("Only active users can be deactivated")
    
    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'role': self.role.value,
            'status': self.status.value,
            'phone': self.phone,
            'email': self.email,
            'is_verified': self.is_verified,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
        }


@event.listens_for(User, 'before_insert')
@event.listens_for(User, 'before_update')
def validate_user_constraints(mapper, connection, target):
    target.validate_username_requirements()


@event.listens_for(User, 'before_update', propagate=True)
def update_timestamp(mapper, connection, target):
    target.updated_at = func.now()
