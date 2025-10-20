from fastapi import APIRouter, Depends
from datetime import datetime

from app.operations.dashboard.get_overview_order_by_day_bar_chart_operation import GetOverviewOrderByDayBarChartOperation
from app.schemas.dashboard.overview import (
    OverviewKeyMetricsQueryParams,
    OverviewKeyMetricsResponse,
    OverviewOrderByDayQueryParams,
    OverviewOrderByDayBarChartResponse,
    OverviewRevenueByDayQueryParams,
    OverviewRevenueByDayBarChartResponse,
)
from app.operations.dashboard.get_dashboard_overview_key_metrics_operation import GetDashboardOverviewKeyMetricsOperation
from app.operations.dashboard.get_overview_revenue_by_day_bar_chart_operation import GetOverviewRevenueByDayBarChartOperation
from app.utils.timezone import get_tzinfo


router = APIRouter()


@router.get("/key-metrics", response_model=OverviewKeyMetricsResponse)
async def get_overview_key_metrics(
    query_params: OverviewKeyMetricsQueryParams = Depends(),
):  
    operation = GetDashboardOverviewKeyMetricsOperation(tenant_id=query_params.tenant_id)
    result = operation.execute()
    return result


@router.get("/order-by-day-bar-chart", response_model=OverviewOrderByDayBarChartResponse)
async def get_overview_order_by_day_bar_chart(
    query_params: OverviewOrderByDayQueryParams = Depends(),
):  
    tzinfo = get_tzinfo()
    now = datetime.now(tzinfo)

    if not query_params.start_date and not query_params.end_date:
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    else:
        start_date = query_params.start_date
        end_date = query_params.end_date

    operation = GetOverviewOrderByDayBarChartOperation(tenant_id=query_params.tenant_id)
    result = operation.execute(
        start_date=start_date,
        end_date=end_date,
    )

    return result


@router.get("/revenue-by-day-bar-chart", response_model=OverviewRevenueByDayBarChartResponse)
async def get_overview_revenue_by_day_bar_chart(
    query_params: OverviewRevenueByDayQueryParams = Depends(),
):  
    tzinfo = get_tzinfo()
    now = datetime.now(tzinfo)

    if not query_params.start_date and not query_params.end_date:
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    else:
        start_date = query_params.start_date
        end_date = query_params.end_date

    operation = GetOverviewRevenueByDayBarChartOperation(tenant_id=query_params.tenant_id)
    result = operation.execute(
        start_date=start_date,
        end_date=end_date,
    )

    return result
