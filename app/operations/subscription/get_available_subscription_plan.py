from typing import List

from sqlalchemy.orm import Session

from app.models.subscription_plan import SubscriptionPlan
from app.models.permission_group import PermissionGroup


class GetAvailableSubscriptionPlanOperation:
    def __init__(self, db: Session):
        self.db = db

    def execute(self) -> List[SubscriptionPlan]:
        return (
            self.db.query(
                *SubscriptionPlan.__table__.columns,
                PermissionGroup.name.label("permission_group_name"),
            )
            .join(PermissionGroup, SubscriptionPlan.permission_group_id == PermissionGroup.id)
            .filter(
                SubscriptionPlan.deleted_at.is_(None),
                SubscriptionPlan.is_enabled.is_(True),
            )
            .order_by(SubscriptionPlan.price.asc())
            .all()
        )
