import uuid

from sqlalchemy import (
    Integer,
    DateTime,
    func,
    Column,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates

from app.libs.database import Base


class PermissionGroupPermission(Base):
    __tablename__ = "permission_group_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())    

    permission_group_id = Column(UUID(as_uuid=True), ForeignKey('permission_groups.id'), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey('permissions.id'), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('permission_group_id', 'permission_id', name='uq_permission_group_permission_group_permission'),
    )

    @validates('permission_group_id')
    def validate_permission_group_id(self, key: str, permission_group_id) -> uuid.UUID:
        if not permission_group_id:
            raise ValueError("Permission group ID is required")
        
        if not isinstance(permission_group_id, uuid.UUID):
            try:
                permission_group_id = uuid.UUID(str(permission_group_id))
            except (ValueError, TypeError):
                raise ValueError("Invalid permission group ID format")
        
        return permission_group_id

    @validates('permission_id')
    def validate_permission_id(self, key: str, permission_id) -> int:
        if not permission_id:
            raise ValueError("Permission ID is required")
        
        if not isinstance(permission_id, int):
            try:
                permission_id = int(permission_id)
            except (ValueError, TypeError):
                raise ValueError("Invalid permission ID format")
        
        return permission_id

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'created_at': self.created_at,
            'permission_group_id': str(self.permission_group_id),
            'permission_id': self.permission_id,
        }
