import uuid

from sqlalchemy import (
    DateTime,
    func,
    Column,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates

from app.libs.database import Base


class StoreMember(Base):
    __tablename__ = "store_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())    

    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('store_id', 'user_id', name='uq_store_member_store_user'),
    )

    @validates('store_id')
    def validate_store_id(self, key: str, store_id) -> uuid.UUID:
        if not store_id:
            raise ValueError("Store ID is required")
        
        if not isinstance(store_id, uuid.UUID):
            try:
                store_id = uuid.UUID(str(store_id))
            except (ValueError, TypeError):
                raise ValueError("Invalid store ID format")
        
        return store_id

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

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'store_id': str(self.store_id),
            'user_id': str(self.user_id),
        }
