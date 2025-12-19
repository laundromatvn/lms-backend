from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.libs.database import get_db
from app.models.user import User
from app.operations.notification.mark_all_notifications_as_seen import MarkAllNotificationsAsSeenOperation
from app.operations.notification.mark_notification_as_seen import MarkNotificationAsSeenOperation

router = APIRouter()


@router.post("/{notification_id}/mark-as-seen", status_code=status.HTTP_204_NO_CONTENT)
def mark_notification_as_seen(
    notification_id: UUID,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        operation = MarkNotificationAsSeenOperation(db, notification_id)
        operation.execute()
    except Exception as e:
        logger.error("Mark notification as seen failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/mark-all-as-seen", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_notifications_as_seen(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        operation = MarkAllNotificationsAsSeenOperation(db, current_user.id)
        operation.execute()
    except Exception as e:
        logger.error("Mark all notifications as seen failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

