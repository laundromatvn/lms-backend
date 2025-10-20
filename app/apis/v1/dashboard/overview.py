import json
from fastapi import APIRouter, Depends
from datetime import datetime

from app.apis.deps import get_current_user
from app.models.user import User
from app.operations.dashboard.list_overview_order_operation import ListOverviewOrderOperation
from app.operations.order import OrderOperation
from app.operations.dashboard.get_overview_order_by_day_bar_chart_operation import GetOverviewOrderByDayBarChartOperation
from app.schemas.dashboard.overview import (
    OverviewKeyMetricsQueryParams,
    OverviewKeyMetricsResponse,
    OverviewOrderByDayQueryParams,
    OverviewOrderByDayBarChartResponse,
    OverviewRevenueByDayQueryParams,
    OverviewRevenueByDayBarChartResponse,
    StoreKeyMetricsListResponse,
    ListOverviewOrdersQueryParams,
    ListOverviewOrdersResponseItem,
)
from app.operations.dashboard.get_dashboard_overview_key_metrics_operation import GetDashboardOverviewKeyMetricsOperation
from app.operations.dashboard.get_overview_revenue_by_day_bar_chart_operation import GetOverviewRevenueByDayBarChartOperation
from app.operations.dashboard.get_overview_store_key_metrics_operation import GetOverviewStoreKeyMetricsOperation
from app.operations.dashboard.list_overview_order_operation import ListOverviewOrderOperation
from app.utils.pagination import get_total_pages
from app.utils.timezone import get_tzinfo
from app.schemas.pagination import PaginatedResponse


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


@router.get("/store-key-metrics", response_model=StoreKeyMetricsListResponse)
async def get_store_key_metrics(
    query_params: OverviewKeyMetricsQueryParams = Depends(),
):  
    operation = GetOverviewStoreKeyMetricsOperation(tenant_id=query_params.tenant_id)
    result = operation.execute()
    return {
        "store_key_metrics": result,
    }


@router.get("/order", response_model=PaginatedResponse[ListOverviewOrdersResponseItem])
async def list_overview_orders(
    query_params: ListOverviewOrdersQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
):
    total, data = ListOverviewOrderOperation.execute(
        current_user=current_user,
        query_params=query_params
    )

    items = []
    for row in data:
        row_dict = dict(row._mapping)
        order = row_dict['Order']
        
        item_dict = {
            "id": order.id,
            "created_at": order.created_at.strftime("%H:%M %d %b %Y"),  # 17:20 17 Aug 2025
            "updated_at": order.updated_at.strftime("%H:%M %d %b %Y"),
            "deleted_at": order.deleted_at.strftime("%H:%M %d %b %Y") if order.deleted_at else None,
            "created_by": order.created_by,
            "updated_by": order.updated_by,
            "deleted_by": order.deleted_by if order.deleted_by else None,
            "total_amount": order.total_amount,
            "total_washer": order.total_washer,
            "total_dryer": order.total_dryer,
            "status": order.status,
            "payment_status": row_dict['payment_status'],
            "transaction_code": row_dict['transaction_code'],
            "payment_method": row_dict['payment_method'],
        }
        items.append(ListOverviewOrdersResponseItem.model_validate(item_dict))
    
    return {
        "page": query_params.page,
        "page_size": query_params.page_size,
        "total": total,
        "total_pages": get_total_pages(total, query_params.page_size),
        "data": items,
    }
