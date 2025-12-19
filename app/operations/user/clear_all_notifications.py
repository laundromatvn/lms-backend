
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.notification import Notification, NotificationChannel


class ClearAllNotificationsOperation:
    """
    This operation clears all notifications for a user.
    Only IN_APP notifications are cleared.
    """

    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def execute(self) -> None:
        self.db.query(Notification).filter(
            Notification.user_id == self.current_user.id,
            Notification.channel == NotificationChannel.IN_APP
        ).delete()
        self.db.commit()
