from typing import List

from fastapi import Query
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.notification import Notification
from app.schemas.user import ListNotificationsQueryParams


class ListNotificationsOperation:
    """
    This operation lists the notifications for a user.
    """

    def __init__(self, db: Session, current_user: User, query_params: ListNotificationsQueryParams):
        self.db = db
        self.current_user = current_user
        self.query_params = query_params

    def execute(self) -> tuple[int, List[Notification]]:
        base_query = (
            self.db.query(Notification)
            .filter(Notification.user_id == self.current_user.id)
        )
        
        base_query = self._apply_filters(base_query)

        total = base_query.count()
        notifications = (
            base_query
            .order_by(Notification.created_at.desc())
            .offset((self.query_params.page - 1) * self.query_params.page_size)
            .limit(self.query_params.page_size)
            .all()
        )

        return total, notifications

    def _apply_filters(self, base_query: Query) -> Query:
        if self.query_params.type:
            base_query = base_query.filter(Notification.type == self.query_params.type)

        return base_query
