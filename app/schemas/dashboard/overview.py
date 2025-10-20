from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel


class OverviewKeyMetricsQueryParams(BaseModel):
    tenant_id: UUID
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
