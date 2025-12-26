from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.subscription_plan import (
    SubscriptionPlan,
    SubscriptionPlanInterval,
    SubscriptionPlanType,
)
from app.models.subscription import Subscription, SubscriptionStatus


class SubscribeToPlanOperation:
    def __init__(
        self,
        db: Session,
        current_user: User,
        tenant_id: UUID,
        subscription_plan_id: UUID,
    ):
        self.db = db
        self.current_user = current_user
        self.tenant_id = tenant_id
        self.subscription_plan_id = subscription_plan_id

    def execute(self):
        self._get_tenant()
        self._get_subscription_plan()
        
        self._validate()

        self._subscribe()

    def _get_tenant(self) -> Tenant:
        self.tenant = (
            self.db.query(Tenant)
            .filter(
                Tenant.id == self.tenant_id,
                Tenant.deleted_at.is_(None),
            )
            .first()
        )
        if not self.tenant:
            raise ValueError("Tenant not found")

    def _get_subscription_plan(self) -> SubscriptionPlan:
        self.subscription_plan = (
            self.db.query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.id == self.subscription_plan_id,
                SubscriptionPlan.is_enabled.is_(True),
                SubscriptionPlan.deleted_at.is_(None),
            )
            .first()
        )
        if not self.subscription_plan:
            raise ValueError("Subscription plan not found")

    def _validate(self):
        self._validate_tenant()
        
    def _validate_tenant(self):
        tenant_member = (
            self.db.query(TenantMember)
            .filter(
                TenantMember.tenant_id == self.tenant_id,
                TenantMember.user_id == self.current_user.id,
                TenantMember.is_enabled.is_(True),
            )
            .first()
        )
        if not tenant_member:
            raise ValueError("Tenant member not found")

    def _subscribe(self):
        now = datetime.now()
        
        # TODO: Update when subscription payment is implemented
        start_date = now
        trial_end_date = self._calculate_trial_end_date(start_date)
        end_date = self._calculate_end_date(start_date, trial_end_date)
        next_renewal_date = self._calculate_next_renewal_date(end_date)

        subscription = Subscription(
            tenant_id=self.tenant_id,
            subscription_plan_id=self.subscription_plan_id,
            status=SubscriptionStatus.ACTIVE,
            start_date=start_date,
            trial_end_date=trial_end_date,
            end_date=end_date,
            next_renewal_date=next_renewal_date,
        )
        self.db.add(subscription)
        self.db.commit()

    def _calculate_trial_end_date(self, start_date: datetime) -> Optional[datetime]:
        existing_subscription = (
            self.db.query(Subscription)
            .filter(
                Subscription.tenant_id == self.tenant_id,
                Subscription.trial_end_date.isnot(None),
            )
            .first()
        )
        if existing_subscription:
            return None

        return start_date + relativedelta(days=self.subscription_plan.trial_period_count)
    
    def _calculate_end_date(self, start_date: datetime, trial_end_date: Optional[datetime]) -> datetime:
        end_date = start_date if not trial_end_date else trial_end_date

        if self.subscription_plan.interval == SubscriptionPlanInterval.MONTH:
            end_date = end_date + relativedelta(months=self.subscription_plan.interval_count)
        elif self.subscription_plan.interval == SubscriptionPlanInterval.YEAR:
            end_date = end_date + relativedelta(years=self.subscription_plan.interval_count)
        else:
            raise ValueError("Invalid interval")

        return end_date

    def _calculate_next_renewal_date(self, end_date: datetime) -> Optional[datetime]:
        if self.subscription_plan.type == SubscriptionPlanType.RECURRING:
            return end_date
        else:
            return None
