from datetime import datetime
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationService:

    LIMIT_PER_DAY = 5

    def __init__(self, db: Session):
        self.db = db

    def add(self, notification: Notification) -> None:
        self.add_bulk([notification])
        
    def add_bulk(self, notifications: List[Notification]) -> None:
        filtered_notifications = self._filter_notifications(notifications)
        if not filtered_notifications: return

        self.db.add_all(filtered_notifications)
        self.db.commit()

    def _filter_notifications(self, notifications: List[Notification]) -> List[Notification]:
        if not notifications: return []

        filtered_notifications = self._filter_reach_limit_per_day(notifications)

        return filtered_notifications

    def _filter_reach_limit_per_day(self, notifications: List[Notification]) -> List[Notification]:
        user_ids = [notification.user_id for notification in notifications]

        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0)
        today_end = now.replace(hour=23, minute=59, second=59)

        over_limit_notifications = (
            self.db.query(Notification.user_id)
            .filter(Notification.user_id.in_(user_ids))
            .filter(Notification.created_at >= today_start)
            .filter(Notification.created_at <= today_end)
            .group_by(Notification.user_id)
            .having(func.count(Notification.id) >= self.LIMIT_PER_DAY)
            .all()
        )
        over_limit_user_ids = [notification.user_id for notification in over_limit_notifications]

        return [
            notification
            for notification in notifications
            if notification.user_id not in over_limit_user_ids]
