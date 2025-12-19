from uuid import UUID

from sqlalchemy.orm import Session

from app.models.notification import Notification


class MarkNotificationAsSeenOperation:
    """
    This operation marks a notification as seen.
    """

    def __init__(self, db: Session, notification_id: UUID):
        self.db = db
        self.notification_id = notification_id

    def execute(self):
        notification = self.db.query(Notification).filter(Notification.id == self.notification_id).first()
        if not notification:
            raise ValueError("Notification not found")

        notification.mark_as_seen()
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        return notification
