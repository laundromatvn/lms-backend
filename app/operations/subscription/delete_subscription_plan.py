from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.subscription_plan import SubscriptionPlan


class DeleteSubscriptionPlanOperation:
    def __init__(self, db: Session, current_user: User, subscription_plan_id: UUID):
        self.db = db
        self.current_user = current_user
        self.subscription_plan_id = subscription_plan_id

    def execute(self):
        # TODO: Check if the subscription plan is used by any tenant
        self._get_subscription_plan()
        self._delete()

    def _get_subscription_plan(self) -> SubscriptionPlan:
        self.subscription_plan = (
            self.db
            .query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.id == self.subscription_plan_id,
                SubscriptionPlan.deleted_at.is_(None),
                SubscriptionPlan.is_default.is_(False),
                SubscriptionPlan.is_enabled.is_(True),
            )
            .first()
        )
        if not self.subscription_plan:
            raise ValueError(f"Subscription plan with ID {self.subscription_plan_id} not found")

    def _delete(self):
        self.subscription_plan.soft_delete(self.current_user.id)
        self.db.add(self.subscription_plan)
        self.db.commit()
