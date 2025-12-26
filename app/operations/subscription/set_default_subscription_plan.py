from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.subscription_plan import SubscriptionPlan


class SetDefaultSubscriptionPlanOperation:
    def __init__(
        self,
        db: Session,
        current_user: User,
        subscription_plan_id: UUID,
    ):
        self.db = db
        self.current_user = current_user
        self.subscription_plan_id = subscription_plan_id

    def execute(self):
        self._get_subscription_plan()
        self._remove_default_from_other_subscription_plans()
        self._set_default()

    def _get_subscription_plan(self) -> SubscriptionPlan:
        self.subscription_plan = (
            self.db.query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.id == self.subscription_plan_id,
                SubscriptionPlan.deleted_at.is_(None),
                SubscriptionPlan.is_enabled.is_(True),
                SubscriptionPlan.is_default.is_(False),
            )
            .first()
        )
        if not self.subscription_plan:
            raise ValueError(
                f"Subscription plan with ID {self.subscription_plan_id} not found"
            )

    def _remove_default_from_other_subscription_plans(self):
        self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.is_default.is_(True),
        ).update({
            "is_default": False,
            "updated_by": self.current_user.id,
            "updated_at": datetime.now(),
        }, synchronize_session=False)
        self.db.commit()

    def _set_default(self):
        self.subscription_plan.is_default = True
        self.subscription_plan.updated_by = self.current_user.id
        self.subscription_plan.updated_at = datetime.now()
        self.db.add(self.subscription_plan)
        self.db.commit()
