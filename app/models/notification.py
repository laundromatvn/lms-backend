from enum import Enum
import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    func,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates

from app.libs.database import Base


class NotificationType(str, Enum):
    INFO = "INFO"
    ERROR = "ERROR"


class NotificationStatus(str, Enum):
    NEW = "NEW"
    DELIVERED = "DELIVERED"
    SEEN = "SEEN"
    FAILED = "FAILED"
    
    
class NotificationChannel(str, Enum):
    IN_APP = "IN_APP"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    seen_at = Column(DateTime(timezone=True), nullable=True)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    type = Column(
        SQLEnum(NotificationType, name="notification_type", create_type=False),
        nullable=False,
        default=NotificationType.INFO,
        index=True
    )
    status = Column(
        SQLEnum(NotificationStatus, name="notification_status", create_type=False),
        nullable=False,
        default=NotificationStatus.NEW,
        index=True
    )
    channel = Column(
        SQLEnum(NotificationChannel, name="notification_channel", create_type=False),
        nullable=False,
        default=NotificationChannel.IN_APP,
        index=True
    )
    title = Column(String(255), nullable=False)
    message = Column(String(500), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")

    @validates('user_id')
    def validate_user_id(self, key: str, user_id) -> uuid.UUID:
        if not isinstance(user_id, uuid.UUID):
            try:
                user_id = uuid.UUID(str(user_id))
            except (ValueError, TypeError):
                raise ValueError("Invalid user ID format")
        return user_id
    
    @validates('type')
    def validate_type(self, key: str, type) -> NotificationType:
        if not isinstance(type, NotificationType):
            try:
                type = NotificationType(type)
            except ValueError:
                raise ValueError("Invalid type: {type}. Must be one of {[t.value for t in NotificationType]}")
        return type
    
    @validates('status')
    def validate_status(self, key: str, status) -> NotificationStatus:
        if not isinstance(status, NotificationStatus):
            try:
                status = NotificationStatus(status)
            except ValueError:
                raise ValueError("Invalid status: {status}. Must be one of {[s.value for s in NotificationStatus]}")
        return status
    
    @validates('channel')
    def validate_channel(self, key: str, channel) -> NotificationChannel:
        if not isinstance(channel, NotificationChannel):
            try:
                channel = NotificationChannel(channel)
            except ValueError:
                raise ValueError("Invalid channel: {channel}. Must be one of {[c.value for c in NotificationChannel]}")
        return channel

    @property
    def is_new(self) -> bool:
        return self.status == NotificationStatus.NEW
    
    @property
    def is_seen(self) -> bool:
        return self.status == NotificationStatus.SEEN
    
    @property
    def is_delivered(self) -> bool:
        return self.status == NotificationStatus.DELIVERED
    
    @property
    def is_failed(self) -> bool:
        return self.status == NotificationStatus.FAILED

    def mark_as_seen(self) -> None:
        self.status = NotificationStatus.SEEN
        self.seen_at = func.now()
    
    def mark_as_delivered(self) -> None:
        self.status = NotificationStatus.DELIVERED
    
    def mark_as_failed(self) -> None:
        self.status = NotificationStatus.FAILED
