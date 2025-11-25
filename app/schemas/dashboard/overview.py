from datetime import datetime
from typing import List, Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.machine import MachineStatus
from app.models.order import OrderStatus
from app.models.payment import PaymentStatus, PaymentMethod
from app.schemas.pagination import Pagination


class OverviewKeyMetricsQueryParams(BaseModel):
    tenant_id: UUID | None = None
    store_id: UUID | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class OverviewKeyMetricsResponse(BaseModel):
    total_active_stores: int = 0
    total_stores: int = 0
    total_in_progress_washers: int = 0
    total_washers: int = 0
    total_in_progress_dryers: int = 0
    total_dryers: int = 0
    total_in_progress_orders: int = 0
    total_finished_orders: int = 0
    today_orders: int = 0
    revenue_by_day: float = 0
    revenue_by_month: float = 0


class OverviewOrderByDayQueryParams(BaseModel):
    tenant_id: UUID
    start_date: datetime | None = None
    end_date: datetime | None = None
    

class OverviewOrderByDayBarChartResponse(BaseModel):
    labels: List[str]
    values: List[float]
    
    
class OverviewRevenueByDayQueryParams(BaseModel):
    tenant_id: UUID
    start_date: datetime | None = None
    end_date: datetime | None = None
    

class OverviewRevenueByDayBarChartResponse(BaseModel):
    labels: List[str]
    values: List[float]


class StoreKeyMetricsResponse(BaseModel):
    id: UUID
    name: str
    address: str
    contact_phone_number: str
    tenant_id: UUID
    total_orders: int = 0
    total_revenue: float = 0
    
    
class StoreKeyMetricsResponse(BaseModel):
    total_active_stores: int = 0
    total_stores: int = 0
    total_in_progress_washers: int = 0
    total_washers: int = 0
    total_in_progress_dryers: int = 0
    total_dryers: int = 0
    total_in_progress_orders: int = 0
    today_orders: int = 0
    revenue_by_day: float = 0
    revenue_by_month: float = 0


class ListOverviewOrdersQueryParams(Pagination):
    tenant_id: Optional[UUID] = None
    store_id: Optional[UUID] = None
    status: Optional[OrderStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    payment_status: Optional[PaymentStatus] = None
    query: Optional[str] = None
    order_by: Optional[str] = None
    order_direction: Optional[str] = None


class ListOverviewOrdersResponseItem(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    created_by: UUID
    updated_by: UUID | None
    deleted_by: UUID | None
    total_amount: float
    total_washer: int
    total_dryer: int
    status: OrderStatus
    payment_status: PaymentStatus
    transaction_code: str
    payment_method: PaymentMethod


class GetOverviewMachineStatusLineChartQueryParams(BaseModel):
    store_id: UUID | None = None
    machine_id: UUID | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class MachineStatusLineChartData(BaseModel):
    date: str
    label: str
    value: str
