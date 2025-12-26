from uuid import UUID

from sqlalchemy.orm import Session, Query

from app.models.permission_group import PermissionGroup
from app.models.user import User
from app.models.subscription_plan import SubscriptionPlan


class GetSubscriptionPlanOperation:
    def __init__(self, db: Session, current_user: User, subscription_plan_id: UUID):
        self.db = db
        self.current_user = current_user
        self.subscription_plan_id = subscription_plan_id

    def execute(self):
        subscription_plan = self._get_subscription_plan()
        if not subscription_plan:
            raise ValueError(f"Subscription plan with ID {self.subscription_plan_id} not found")

        return subscription_plan

    def _get_subscription_plan(self) -> SubscriptionPlan:
        return (
            self.db
            .query(
                *SubscriptionPlan.__table__.columns,
                PermissionGroup.name.label("permission_group_name"),
            )
            .join(PermissionGroup, SubscriptionPlan.permission_group_id == PermissionGroup.id)
            .filter(
                SubscriptionPlan.id == self.subscription_plan_id,
                SubscriptionPlan.deleted_at.is_(None),
            )
            .first()
        )
