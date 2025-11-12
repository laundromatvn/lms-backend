from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.controller import ControllerStatus
from app.models.firmware import FirmwareStatus, FirmwareVersionType
from app.models.firmware_deployment import FirmwareDeploymentStatus
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


class ListProvisionedControllersQueryParams(Pagination):
    tenant_id: UUID | None = None
    store_id: UUID | None = None
    search: str | None = None
    order_by: str | None = None
    order_direction: str | None = None


class ProvisionedControllerSerializer(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    status: ControllerStatus
    device_id: str
    name: str | None = None
    store_id: UUID | None = None
    store_name: str | None = None
    tenant_id: UUID | None = None
    tenant_name: str | None = None
    firmware_id: UUID | None = None
    firmware_name: str | None = None
    firmware_version: str | None = None


class ProvisionFirmwareSchema(BaseModel):
    all_controllers: bool = False
    controller_ids: list[UUID] | None = None


class ListProvisioningControllersQueryParams(Pagination):
    deployment_status: FirmwareDeploymentStatus | None = None
    search: str | None = None
    order_by: str | None = None
    order_direction: str | None = None


class ProvisioningControllerSerializer(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    status: ControllerStatus
    device_id: str
    name: str | None = None
    store_id: UUID | None = None
    store_name: str | None = None
    tenant_id: UUID | None = None
    tenant_name: str | None = None
    firmware_id: UUID | None = None
    firmware_name: str | None = None
    firmware_version: str | None = None
    deployment_id: UUID | None = None
    deployment_status: FirmwareDeploymentStatus | None = None

