from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.subscription import SubscriptionStatus
from app.models.subscription_plan import SubscriptionPlanInterval, SubscriptionPlanType
from app.schemas.pagination import Pagination


class SubscriptionPlanSerializer(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_by: UUID | None = None
    name: str
    description: str | None = None
    is_enabled: bool | None = None
    is_default: bool | None = None
    price: Decimal
    type: SubscriptionPlanType
    interval: SubscriptionPlanInterval | None = None
    interval_count: int | None = None
    trial_period_count: int | None = None
    permission_group_id: UUID | None = None
    permission_group_name: str | None = None


class SubscriptionPlanCreatePayload(BaseModel):
    name: str
    description: str | None = None
    is_enabled: bool | None = None
    is_default: bool | None = None
    price: int
    type: SubscriptionPlanType
    interval: SubscriptionPlanInterval | None = None
    interval_count: int | None = None
    trial_period_count: int | None = None
    permission_group_id: UUID | None = None


class SubscriptionPlanUpdatePayload(BaseModel):
    name: str | None = None
    description: str | None = None
    is_enabled: bool | None = None
    price: int | None = None
    type: SubscriptionPlanType | None = None
    interval: SubscriptionPlanInterval | None = None
    interval_count: int | None = None
    trial_period_count: int | None = None
    permission_group_id: UUID | None = None


class ListSubscriptionPlansQueryParams(Pagination):
    is_enabled: bool | None = None
    is_default: bool | None = None
    search: str | None = None
    order_by: str | None = None
    order_direction: str | None = None


class ListSubscriptionPlansPermissionsQueryParams(Pagination):
    search: str | None = None
    order_by: str | None = None
    order_direction: str | None = None


class SetDefaultSubscriptionPlanPayload(BaseModel):
    subscription_plan_id: UUID


class TenantSubscriptionSerializer(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_by: UUID | None = None
    status: SubscriptionStatus
    start_date: datetime
    end_date: datetime | None = None
    trial_end_date: datetime | None = None
    next_renewal_date: datetime | None = None
    tenant_id: UUID
    subscription_plan_id: UUID
    subscription_plan: SubscriptionPlanSerializer
