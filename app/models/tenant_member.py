import uuid

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates

from app.libs.database import Base


class TenantMember(Base):
    __tablename__ = "tenant_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    is_enabled = Column(Boolean, nullable=False, default=True, index=True)

    # Ensure unique combination of tenant_id and user_id
    __table_args__ = (
        UniqueConstraint('tenant_id', 'user_id', name='uq_tenant_member_tenant_user'),
    )

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

    @validates('user_id')
    def validate_user_id(self, key: str, user_id) -> uuid.UUID:
        if not user_id:
            raise ValueError("User ID is required")
        
        if not isinstance(user_id, uuid.UUID):
            try:
                user_id = uuid.UUID(str(user_id))
            except (ValueError, TypeError):
                raise ValueError("Invalid user ID format")
        
        return user_id

    @validates('is_enabled')
    def validate_is_enabled(self, key: str, is_enabled) -> bool:
        if not isinstance(is_enabled, bool):
            raise ValueError("is_enabled must be a boolean value")
        return is_enabled

    def is_active(self) -> bool:
        """Check if the tenant member is active (enabled)."""
        return self.is_enabled

    def enable(self) -> None:
        """Enable the tenant member."""
        if not self.is_enabled:
            self.is_enabled = True
        else:
            raise ValueError("Tenant member is already enabled")

    def disable(self) -> None:
        """Disable the tenant member."""
        if self.is_enabled:
            self.is_enabled = False
        else:
            raise ValueError("Tenant member is already disabled")

    def to_dict(self) -> dict:
        """Convert the tenant member to a dictionary representation."""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'user_id': str(self.user_id),
            'is_enabled': self.is_enabled,
        }

    def __repr__(self) -> str:
        return f"<TenantMember(id={self.id}, tenant_id={self.tenant_id}, user_id={self.user_id}, is_enabled={self.is_enabled})>"
