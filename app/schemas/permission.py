from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

from app.schemas.pagination import Pagination


class PermissionSerializer(BaseModel):
    id: int
    code: str
    name: str | None = None
    description: str | None = None
    is_enabled: bool


class PermissionCreateRequest(BaseModel):
    code: str
    name: str
    description: str | None = None
    is_enabled: bool


class PermissionEditRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_enabled: bool | None = None


class ListPermissionQueryParams(Pagination):
    is_enabled: bool | None = None
    search: str | None = None
    order_by: str | None = None
    order_direction: str | None = None


class PermissionGroupSerializer(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    updated_by: UUID | None = None
    name: str
    description: str | None = None
    is_enabled: bool
    tenant_id: UUID | None = None


class PermissionGroupCreatePayload(BaseModel):
    name: str
    description: str | None = None
    is_enabled: bool
    tenant_id: UUID | None = None
    
    
class PermissionGroupUpdatePayload(BaseModel):
    name: str | None = None
    description: str | None = None
    is_enabled: bool | None = None
    tenant_id: UUID | None = None


class ListPermissionGroupsQueryParams(Pagination):
    tenant_id: UUID | None = None
    search: str | None = None
    order_by: str | None = None
    order_direction: str | None = None
