"""
Order API endpoints.

This module contains all FastAPI endpoints for order management including
CRUD operations, status updates, and order retrieval.
"""

import uuid
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.libs.database import get_db_session
from app.models.order import OrderStatus
from app.models.user import User
from app.operations.order import OrderOperation, OrderDetailOperation
from app.schemas.order import (
    CreateOrderRequest,
    CreateOrderDetailRequest,
    UpdateOrderStatusRequest,
    OrderResponse,
    OrderDetailResponse,
    OrderListResponse,
    OrderDetailListResponse,
    OrderStatsResponse,
)

router = APIRouter()


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    request: CreateOrderRequest,
    user: User = Depends(get_current_user)
):
    """
    Create a new order.
    
    This endpoint creates a new order with the specified machine selections.
    The order will be created with status NEW and then moved to WAITING_FOR_PAYMENT.
    """
    try:
        order = OrderOperation.create_order(request, user.id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID = Path(..., description="Order ID"),
    _: User = Depends(get_current_user)
):
    """
    Get order by ID.
    
    Returns the order with all its details including machine information.
    """
    try:
        order = OrderOperation.get_order_by_id(order_id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    store_id: Optional[uuid.UUID] = Query(None, description="Filter by store ID"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    _: User = Depends(get_current_user)
):
    """
    List orders with pagination and filtering.
    
    Returns a paginated list of orders with optional filtering by store, status, and date range.
    """
    if store_id:
        result = OrderOperation.get_orders_by_store(
            store_id=store_id,
            page=page,
            per_page=per_page,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
    else:
        # For now, we'll implement a simple version without store filtering
        # In a real implementation, you'd have a more comprehensive list method
        raise HTTPException(status_code=501, detail="Global order listing not implemented yet")
    
    orders = [
        OrderResponse(
            id=order.id,
            created_at=order.created_at,
            updated_at=order.updated_at,
            status=order.status,
            total_amount=order.total_amount,
            total_washer=order.total_washer,
            total_dryer=order.total_dryer,
            store_id=order.store_id,
            store_name=order.store.name if order.store else None,
            order_details=[]
        )
        for order in result['orders']
    ]
    
    return OrderListResponse(
        orders=orders,
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        total_pages=result['total_pages']
    )
