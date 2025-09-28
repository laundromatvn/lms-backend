from uuid import UUID

from pydantic import BaseModel


class TenantMemberSerializer(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    is_enabled: bool


class TenantMemberCreate(BaseModel):
    tenant_id: str
    user_id: str


class TenantMemberUpdate(BaseModel):
    is_enabled: bool
