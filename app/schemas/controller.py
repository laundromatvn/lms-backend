from datetime import datetime
from pydantic import BaseModel
from uuid import UUID

from app.models.controller import ControllerStatus
from app.schemas.pagination import Pagination


class ControllerSerializer(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    status: ControllerStatus
    device_id: str
    name: str | None = None
    store_id: UUID | None = None
    total_relays: int


class AddControllerRequest(BaseModel):
    device_id: str
    name: str | None = None
    store_id: UUID | None = None
    total_relays: int = 1


class UpdateControllerRequest(BaseModel):
    name: str | None = None
    store_id: UUID | None = None
    total_relays: int | None = None


class ListControllerQueryParams(Pagination):
    status: ControllerStatus | None = None
    store_id: UUID | None = None
