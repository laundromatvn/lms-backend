from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.pagination import Pagination
from app.models.store import StoreStatus


class StoreSerializer(BaseModel):
    id: UUID
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None
    status: StoreStatus
    name: str
    address: str
    longitude: float | None = None
    latitude: float | None = None
    contact_phone_number: str
    tenant_id: UUID
    
    
class ListStoreQueryParams(Pagination):
    tenant_id: UUID | None = None
    status: StoreStatus | None = None


class AddStoreRequest(BaseModel):
    name: str
    address: str
    longitude: float | None = None
    latitude: float | None = None
    contact_phone_number: str
    tenant_id: UUID


class UpdateStoreRequest(BaseModel):
    name: str | None = None
    address: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    contact_phone_number: str | None = None
    tenant_id: UUID | None = None
