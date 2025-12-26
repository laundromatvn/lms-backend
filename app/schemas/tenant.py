from datetime import datetime
from pydantic import BaseModel
from uuid import UUID

from app.models.tenant import TenantStatus
from app.schemas.pagination import Pagination


class AddTenantRequest(BaseModel):
    name: str
    contact_email: str
    contact_phone_number: str
    contact_full_name: str
    contact_address: str


class UpdateTenantRequest(BaseModel):
    status: TenantStatus | None = None
    name: str | None = None
    contact_email: str | None = None
    contact_phone_number: str | None = None
    contact_full_name: str | None = None
    contact_address: str | None = None


class TenantSerializer(BaseModel):
    id: UUID
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None
    status: TenantStatus
    name: str
    contact_email: str
    contact_phone_number: str
    contact_full_name: str
    contact_address: str


class ListTenantQueryParams(Pagination):
    status: TenantStatus | None = None
    search: str | None = None
    order_by: str | None = None
    order_direction: str | None = None


class CreateTenantSubscriptionPlanRequest(BaseModel):
    subscription_plan_id: UUID
