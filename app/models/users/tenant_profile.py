import uuid
import re
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates, relationship

from app.core.database import Base


class TenantProfile(Base):
    """
    TenantProfile model for laundry management system.
    
    Represents a tenant's business profile with contact information.
    Each TenantProfile belongs to exactly one User (1-1 relationship).
    """
    
    __tablename__ = "tenant_profiles"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to User - the user who owns/updates this profile
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        unique=True,  # One profile per user
        index=True
    )
    
    # Contact information
    contact_email = Column(String(255), nullable=False, index=True)
    contact_phone = Column(String(20), nullable=False, index=True)
    
    # Optional address field
    address = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="tenant_profile", uselist=False)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_tenant_profile_user_id'),
    )
    
    @validates('contact_email')
    def validate_contact_email(self, key, email):
        """Validate email format using comprehensive regex pattern."""
        if not email:
            raise ValueError("Contact email is required")
        
        # Comprehensive email validation regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        # Additional checks
        if len(email) > 254:  # RFC 5321 limit
            raise ValueError("Email address too long")
        
        local_part, domain = email.split('@')
        if len(local_part) > 64:  # RFC 5321 limit
            raise ValueError("Email local part too long")
        
        return email.lower().strip()
    
    @validates('contact_phone')
    def validate_contact_phone(self, key, phone):
        """Validate phone number format using E.164 standard."""
        if not phone:
            raise ValueError("Contact phone is required")
        
        # Remove all non-digit characters except +
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        
        # E.164 format validation
        if cleaned_phone.startswith('+'):
            # International format: +[country code][number]
            if len(cleaned_phone) < 8 or len(cleaned_phone) > 16:
                raise ValueError("Invalid international phone number length")
            if not re.match(r'^\+[1-9]\d{7,14}$', cleaned_phone):
                raise ValueError("Invalid international phone number format")
        else:
            # National format: assume US/Canada if no country code
            if len(cleaned_phone) == 10:
                # Add +1 for US/Canada
                cleaned_phone = '+1' + cleaned_phone
            elif len(cleaned_phone) == 11 and cleaned_phone.startswith('1'):
                # Already has country code
                cleaned_phone = '+' + cleaned_phone
            else:
                raise ValueError("Invalid phone number format")
        
        return cleaned_phone
    
    @validates('address')
    def validate_address(self, key, address):
        """Validate address field if provided."""
        if address is not None:
            address = address.strip()
            if len(address) > 500:
                raise ValueError("Address too long (max 500 characters)")
            if len(address) < 5:
                raise ValueError("Address too short (min 5 characters)")
        
        return address
    
    def __repr__(self) -> str:
        return f"<TenantProfile(id={self.id}, user_id={self.user_id}, email={self.contact_email})>"
    
    def to_dict(self) -> dict:
        """Convert model instance to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
