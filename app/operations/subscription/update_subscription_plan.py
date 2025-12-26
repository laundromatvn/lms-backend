from uuid import UUID

from sqlalchemy.orm import Session, Query

from app.models.user import User
from app.models.subscription_plan import SubscriptionPlan
from app.schemas.subscription import SubscriptionPlanUpdatePayload


class UpdateSubscriptionPlanOperation:
    def __init__(
        self,
        db: Session,
        current_user: User,
        subscription_plan_id: UUID,
        payload: SubscriptionPlanUpdatePayload,
    ):
        self.db = db
        self.current_user = current_user
        self.subscription_plan_id = subscription_plan_id
        self.payload = payload

    def execute(self):
        self._get_subscription_plan()
        self._update()

    def _get_subscription_plan(self) -> SubscriptionPlan:
        self.subscription_plan = (
            self.db
            .query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.id == self.subscription_plan_id,
                SubscriptionPlan.deleted_at.is_(None),
            )
            .first()
        )
        if not self.subscription_plan:
            raise ValueError(f"Subscription plan with ID {self.subscription_plan_id} not found")

    def _update(self):
        self.subscription_plan.name = self.payload.name
        self.subscription_plan.description = self.payload.description
        self.subscription_plan.is_enabled = self.payload.is_enabled
        self.subscription_plan.is_default = self.payload.is_default
        self.subscription_plan.price = self.payload.price
        self.subscription_plan.type = self.payload.type
        self.subscription_plan.interval = self.payload.interval
        self.subscription_plan.interval_count = self.payload.interval_count
        self.subscription_plan.trial_period_count = self.payload.trial_period_count
        self.subscription_plan.permission_group_id = self.payload.permission_group_id
        
        self.db.add(self.subscription_plan)
        self.db.commit()
