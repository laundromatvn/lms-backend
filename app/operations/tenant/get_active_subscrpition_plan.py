from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.subscription import Subscription, SubscriptionStatus
from app.models.subscription_plan import SubscriptionPlan
from app.models.tenant_member import TenantMember
from app.models.user import User


class GetTenantSubscriptionPlanOperation:
    def __init__(self, db: Session, current_user: User, tenant_id: UUID):
        self.db = db
        self.current_user = current_user
        self.tenant_id = tenant_id

    def execute(self) -> Optional[SubscriptionPlan]:
        self._get_current_active_subscription()
        if not self.subscription:
            return None

        self._get_active_subscription_plan()
        self._validate_tenant_subscription()

        return self.subscription_plan

    def _get_current_active_subscription(self) -> Subscription:
        self.subscription = (
            self.db.query(Subscription)
            .filter(
                Subscription.tenant_id == self.tenant_id,
                Subscription.deleted_at.is_(None),
                Subscription.status.in_([
                    SubscriptionStatus.PENDING,
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.PAST_DUE,
                ]),
            )
            .order_by(Subscription.created_at.desc())
            .first()
        )

    def _get_active_subscription_plan(self) -> SubscriptionPlan:
        self.subscription_plan = (
            self.db.query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.id == self.subscription.subscription_plan_id,
                SubscriptionPlan.deleted_at.is_(None),
                SubscriptionPlan.is_enabled.is_(True),
            )
            .first()
        )
        if not self.subscription_plan:
            raise ValueError("No active subscription plan found")

    def _validate_tenant_subscription(self) -> None:
        self.tenant_member = (
            self.db.query(TenantMember)
            .filter(
                TenantMember.tenant_id == self.tenant_id,
                TenantMember.user_id == self.current_user.id,
                TenantMember.is_enabled.is_(True),
            )
            .first()
        )
        if not self.tenant_member:
            raise ValueError("You are not allowed to get the active subscription plan")
