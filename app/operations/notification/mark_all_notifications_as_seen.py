from uuid import UUID

from sqlalchemy.orm import Session

from app.models.notification import Notification


class MarkAllNotificationsAsSeenOperation:
    """
    This operation marks all notifications as seen for a user.
    """

    def __init__(self, db: Session, user_id: UUID):
        self.db = db
        self.user_id = user_id

    def execute(self):
        notifications = self.db.query(Notification).filter(Notification.user_id == self.user_id).all()
        for notification in notifications:
            notification.mark_as_seen()
            self.db.add(notification)
        self.db.commit()
