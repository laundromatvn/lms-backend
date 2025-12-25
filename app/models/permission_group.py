import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    func,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.libs.database import Base


class PermissionGroup(Base):
    __tablename__ = "permission_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())   
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    name = Column(String(255), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    is_enabled = Column(Boolean, nullable=False, default=True)

    # tenant_id = None: global permission group
    # tenant_id = tenant.id: tenant specific permission group
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=True, index=True)

    tenant = relationship("Tenant", back_populates="permission_groups")
    subscription_plans = relationship("SubscriptionPlan", back_populates="permission_group")
