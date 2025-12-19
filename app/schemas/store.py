from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel

from app.models.store import StoreStatus
from app.schemas.machine import MachineSerializer
from app.schemas.pagination import Pagination



class QRPaymentMethodDetails(BaseModel):
    bank_code: str | None = None
    bank_name: str | None = None
    bank_account_number: str | None = None
    bank_account_name: str | None = None
    
    
class VNPAYPaymentMethodDetails(BaseModel):
    merchant_code: str | None = None
    terminal_code: str | None = None
    init_secret_key: str | None = None
    query_secret_key: str | None = None
    ipnv3_secret_key: str | None = None


class PaymentMethod(BaseModel):
    payment_method: str
    payment_provider: str | None = None
    is_enabled: bool
    details: Any | None = None


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
    tenant_name: str | None = None
    payment_details: Optional[Dict[str, Any]] = None
    payment_methods: List[PaymentMethod] = []
    
    
class ListStoreQueryParams(Pagination):
    tenant_id: UUID | None = None
    status: StoreStatus | None = None
    search: str | None = None
    order_by: str | None = None
    order_direction: str | None = None


class AddStoreRequest(BaseModel):
    name: str
    address: str
    longitude: float | None = None
    latitude: float | None = None
    contact_phone_number: str
    tenant_id: UUID
    payment_methods: List[PaymentMethod] = []


class UpdateStoreRequest(BaseModel):
    name: str | None = None
    address: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    contact_phone_number: str | None = None
    tenant_id: UUID | None = None
    payment_methods: List[PaymentMethod] | None = None


class ClassifiedMachinesResponse(BaseModel):
    washers: List[MachineSerializer]
    dryers: List[MachineSerializer]


class StorePaymentMethod(BaseModel):
    payment_method: str
    payment_provider: str | None = None
