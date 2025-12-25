from sqlalchemy.orm import Session

from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.models.permission_group import PermissionGroup
from app.schemas.subscription import SubscriptionPlanCreatePayload


class AddSubscriptionPlanOperation:
    def __init__(self, db: Session, current_user: User, payload: SubscriptionPlanCreatePayload):
        self.db = db
        self.current_user = current_user
        self.payload = payload

    def execute(self):
        self._validate()
        self._add()

    def _add(self):
        subscription_plan = SubscriptionPlan(
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
            name=self.payload.name,
            description=self.payload.description,
            is_enabled=self.payload.is_enabled,
            is_default=self.payload.is_default,
            price=self.payload.price,
            type=self.payload.type,
            interval=self.payload.interval,
            interval_count=self.payload.interval_count,
            trial_period_count=self.payload.trial_period_count,
            permission_group_id=self.payload.permission_group_id,
        )
        self.db.add(subscription_plan)
        self.db.commit()

    def _validate(self):
        self.permission_group = self.db.query(PermissionGroup).filter(
            PermissionGroup.id == self.payload.permission_group_id,
            PermissionGroup.tenant_id == None
        ).first()
        if not self.permission_group:
            raise ValueError("Permission group not found")
