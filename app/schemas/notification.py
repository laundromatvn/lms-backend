from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

from app.models.notification import NotificationType, NotificationStatus, NotificationChannel


class NotificationSerializer(BaseModel):
    id: UUID
    created_at: datetime
    seen_at: datetime | None = None
    type: NotificationType
    status: NotificationStatus
    channel: NotificationChannel
    title: str
    message: str
