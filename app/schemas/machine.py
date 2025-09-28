from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID

from app.models.machine import MachineType, MachineStatus
from app.schemas.pagination import Pagination


class MachineSerializer(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    controller_id: UUID
    relay_no: int
    name: str | None = None
    machine_type: MachineType
    details: Dict[str, Any] = {}
    base_price: Decimal
    status: MachineStatus


class AddMachineRequest(BaseModel):
    controller_id: UUID
    relay_no: int = Field(..., ge=1, le=50)
    name: str | None = Field(None, min_length=1, max_length=255)
    machine_type: MachineType
    details: Dict[str, Any] = {}
    base_price: Decimal = Field(default=Decimal('0.00'), ge=0)


class UpdateMachineRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    machine_type: MachineType | None = None
    details: Dict[str, Any] = {}
    base_price: Decimal | None = Field(None, ge=0)
    status: MachineStatus | None = None


class ListMachineQueryParams(Pagination):
    controller_id: UUID | None = None
    store_id: UUID | None = None
    machine_type: MachineType | None = None
    status: MachineStatus | None = None
