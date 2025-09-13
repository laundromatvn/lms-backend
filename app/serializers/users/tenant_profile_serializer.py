from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
import re


class TenantProfileBase(BaseModel):
    """Base serializer for TenantProfile with common fields."""
    contact_email: EmailStr
    contact_phone: str
    address: Optional[str] = None
    
    @validator('contact_phone')
    def validate_contact_phone(cls, v):
        """Validate phone number format using E.164 standard."""
        if not v:
            raise ValueError("Contact phone is required")
        
        # Remove all non-digit characters except +
        cleaned_phone = re.sub(r'[^\d+]', '', v)
        
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
    
    @validator('address')
    def validate_address(cls, v):
        """Validate address field if provided."""
        if v is not None:
            v = v.strip()
            if len(v) > 500:
                raise ValueError("Address too long (max 500 characters)")
            if len(v) < 5:
                raise ValueError("Address too short (min 5 characters)")
        
        return v


class TenantProfileCreate(TenantProfileBase):
    """Serializer for creating a new TenantProfile."""
    pass


class TenantProfileUpdate(BaseModel):
    """Serializer for updating an existing TenantProfile."""
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    
    @validator('contact_phone')
    def validate_contact_phone(cls, v):
        """Validate phone number format using E.164 standard."""
        if v is not None:
            # Remove all non-digit characters except +
            cleaned_phone = re.sub(r'[^\d+]', '', v)
            
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
        
        return v
    
    @validator('address')
    def validate_address(cls, v):
        """Validate address field if provided."""
        if v is not None:
            v = v.strip()
            if len(v) > 500:
                raise ValueError("Address too long (max 500 characters)")
            if len(v) < 5:
                raise ValueError("Address too short (min 5 characters)")
        
        return v


class TenantProfileResponse(TenantProfileBase):
    """Serializer for TenantProfile API responses."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TenantProfileSerializer(BaseModel):
    """Legacy serializer for backward compatibility."""
    id: Optional[str] = None
    user_id: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
