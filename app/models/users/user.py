"""
User model implementation with role-based validation and password hashing.
"""

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
    """User role enumeration."""
    ADMIN = "ADMIN"
    TENANT = "TENANT"
    TENANT_STAFF = "TENANT_STAFF"
    CUSTOMER = "CUSTOMER"


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """
    User model with role-based validation and password hashing.
    
    Fields:
        id: UUID primary key
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
        email: Unique email address (required for admin, tenant, tenant-staff)
        phone: Unique phone number (required for customer)
        password: Hashed password
        role: User role (admin, tenant, tenant-staff, customer)
        is_verified: Whether user is verified via activation token
        verified_at: Timestamp when user was verified
    """
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # User identification
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    
    # Authentication
    password = Column(String(255), nullable=False)
    
    # User role and verification
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format and uniqueness requirements."""
        if email is not None:
            # Basic email format validation
            if '@' not in email or '.' not in email.split('@')[1]:
                raise ValueError("Invalid email format")
            
            # Check if email is required for this role
            if self.role in [UserRole.ADMIN, UserRole.TENANT, UserRole.TENANT_STAFF] and not email:
                raise ValueError(f"Email is required for role: {self.role}")
        
        return email
    
    @validates('phone')
    def validate_phone(self, key, phone):
        """Validate phone format and requirements."""
        if phone is not None:
            # Basic phone format validation (digits, +, -, spaces, parentheses)
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
        """Validate role-based field requirements."""
        # This validation runs after email and phone validations
        # We need to check the current state of the object
        if role == UserRole.CUSTOMER:
            if not self.phone:
                raise ValueError("Phone is required for customer role")
        elif role in [UserRole.ADMIN, UserRole.TENANT, UserRole.TENANT_STAFF]:
            if not self.email:
                raise ValueError(f"Email is required for role: {role}")
        
        return role
    
    @classmethod
    def set_password(cls, plain_password: str) -> None:
        """
        Hash and set the user's password.
        
        Args:
            plain_password: Plain text password to hash and store
        """
        return pwd_context.hash(plain_password)
    
    def verify_password(self, plain_password: str) -> bool:
        """
        Verify a plain password against the stored hash.
        
        Args:
            plain_password: Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, self.password)
    
    def verify_user(self) -> None:
        """Mark user as verified and set verification timestamp."""
        self.is_verified = True
        self.verified_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(id={self.id}, email={self.email}, phone={self.phone}, role={self.role})>"
    
    def to_dict(self) -> dict:
        """Convert user to dictionary representation."""
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
