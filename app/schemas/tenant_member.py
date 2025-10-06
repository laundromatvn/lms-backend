from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TenantMemberSerializer(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    is_enabled: bool
    tenant_name: str | None
    user_email: str | None
    user_phone: str | None
    user_role: str | None
    user_status: str | None


class TenantMemberCreate(BaseModel):
    tenant_id: str
    user_id: str


class TenantMemberUpdate(BaseModel):
    is_enabled: bool


class ListTenantMemberQueryParams(BaseModel):
    tenant_id: Optional[UUID] = None
    page: int = 1
    page_size: int = 10
