import uuid
from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates
from passlib.context import CryptContext

from app.core.database import Base


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    TENANT = "TENANT"
    TENANT_STAFF = "TENANT_STAFF"
    CUSTOMER = "CUSTOMER"


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    
    password = Column(String(255), nullable=False)
    
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    
    @validates('email')
    def validate_email(self, key, email):
        if email is not None:
            if '@' not in email or '.' not in email.split('@')[1]:
                raise ValueError("Invalid email format")
            
            if self.role in [UserRole.ADMIN, UserRole.TENANT, UserRole.TENANT_STAFF] and not email:
                raise ValueError(f"Email is required for role: {self.role}")
        
        return email
    
    @validates('phone')
    def validate_phone(self, key, phone):
        if phone is not None:
            import re
            
            if phone.startswith('+'):
                phone = phone[1:]
                
            if phone.startswith('0'):
                phone = phone[1:]
            
            phone_pattern = r'^[\+]?[0-9\s\-\(\)]{9}$'
            if not re.match(phone_pattern, phone):
                raise ValueError("Invalid phone format")
        
        return phone
    
    @validates('role')
    def validate_role_requirements(self, key, role):
        if role == UserRole.CUSTOMER:
            if not self.phone:
                raise ValueError("Phone is required for customer role")
        elif role in [UserRole.ADMIN, UserRole.TENANT, UserRole.TENANT_STAFF]:
            if not self.email:
                raise ValueError(f"Email is required for role: {role}")
        
        return role
    
    @classmethod
    def set_password(cls, plain_password: str) -> None:
        return pwd_context.hash(plain_password)
    
    def verify_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self.password)
    
    def verify_user(self) -> None:
        self.is_verified = True
        self.verified_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, phone={self.phone}, role={self.role})>"
    
    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'email': self.email,
            'phone': self.phone,
            'role': self.role.value if self.role else None,
            'is_verified': self.is_verified,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
        }
