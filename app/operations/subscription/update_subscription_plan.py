from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

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
        for key, value in self.payload.model_dump().items():
            if value is not None:
                setattr(self.subscription_plan, key, value)
        
        self.subscription_plan.updated_by = self.current_user.id
        self.subscription_plan.updated_at = datetime.now()

        self.db.add(self.subscription_plan)
        self.db.commit()
