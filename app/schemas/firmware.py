from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.firmware import FirmwareStatus, FirmwareVersionType
from app.schemas.pagination import Pagination


class FirmwareSerializer(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    created_by: UUID
    updated_by: UUID
    deleted_by: UUID | None = None
    name: str
    version: str
    description: str | None = None
    status: FirmwareStatus
    version_type: FirmwareVersionType
    object_name: str
    file_size: int
    checksum: str


class FirmwareCreateSchema(BaseModel):
    name: str
    version: str
    description: str | None = None
    status: FirmwareStatus = FirmwareStatus.DRAFT
    version_type: FirmwareVersionType = FirmwareVersionType.PATCH
    object_name: str
    
    
class FirmwareUpdateSchema(BaseModel):
    name: str | None = None
    version: str | None = None
    description: str | None = None
    status: FirmwareStatus | None = None
    version_type: FirmwareVersionType | None = None


class ListFirmwareQueryParams(Pagination):
    status: FirmwareStatus | None = None
    version_type: FirmwareVersionType | None = None
    search: str | None = None
    order_by: str | None = None
    order_direction: str | None = None

