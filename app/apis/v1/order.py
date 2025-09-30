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


@router.post("/", response_model=OrderResponse, status_code=201)
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


@router.get("/", response_model=OrderListResponse)
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


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: uuid.UUID = Path(..., description="Order ID"),
    request: UpdateOrderStatusRequest = ...,
    user: User = Depends(get_current_user)
):
    """
    Update order status.
    
    Updates the order status with proper validation and state transitions.
    """
    try:
        order = OrderOperation.update_order_status(order_id, request, user.id)
        
        return OrderResponse(
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: uuid.UUID = Path(..., description="Order ID"),
    user: User = Depends(get_current_user)
):
    """
    Cancel an order.
    
    Cancels the order and frees up all associated machines.
    """
    try:
        order = OrderOperation.cancel_order(order_id, user.id)
        
        return OrderResponse(
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stores/{store_id}/orders", response_model=OrderListResponse)
async def get_store_orders(
    store_id: uuid.UUID = Path(..., description="Store ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    _: User = Depends(get_current_user)
):
    """
    Get orders for a specific store.
    
    Returns a paginated list of orders for the specified store.
    """
    result = OrderOperation.get_orders_by_store(
        store_id=store_id,
        page=page,
        per_page=per_page,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    
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


@router.get("/stores/{store_id}/statistics", response_model=OrderStatsResponse)
async def get_store_order_statistics(
    store_id: uuid.UUID = Path(..., description="Store ID"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
):
    """
    Get order statistics for a store.
    
    Returns comprehensive statistics about orders for the specified store.
    """
    stats = OrderOperation.get_order_statistics(
        store_id=store_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return OrderStatsResponse(**stats)


@router.post("/{order_id}/details", response_model=OrderDetailResponse, status_code=201)
async def create_order_detail(
    order_id: uuid.UUID = Path(..., description="Order ID"),
    request: CreateOrderDetailRequest = ...,
    _: User = Depends(get_current_user)
):
    """
    Add a new order detail to an existing order.
    
    Adds a machine booking to an existing order.
    """
    try:
        order_detail = OrderDetailOperation.create_order_detail(order_id, request)
        
        return OrderDetailResponse(
            id=order_detail.id,
            created_at=order_detail.created_at,
            updated_at=order_detail.updated_at,
            status=order_detail.status,
            machine_id=order_detail.machine_id,
            order_id=order_detail.order_id,
            add_ons=order_detail.add_ons,
            price=order_detail.price,
            machine_name=order_detail.machine.name if order_detail.machine else None,
            machine_type=order_detail.machine.machine_type if order_detail.machine else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{order_id}/details", response_model=OrderDetailListResponse)
async def get_order_details(
    order_id: uuid.UUID = Path(..., description="Order ID"),
    _: User = Depends(get_current_user)
):
    """
    Get all order details for an order.
    
    Returns all machine bookings for the specified order.
    """
    order_details = OrderDetailOperation.get_order_details_by_order(order_id)
    
    details = [
        OrderDetailResponse(
            id=detail.id,
            created_at=detail.created_at,
            updated_at=detail.updated_at,
            status=detail.status,
            machine_id=detail.machine_id,
            order_id=detail.order_id,
            add_ons=detail.add_ons,
            price=detail.price,
            machine_name=detail.machine.name if detail.machine else None,
            machine_type=detail.machine.machine_type if detail.machine else None
        )
        for detail in order_details
    ]
    
    return OrderDetailListResponse(
        order_details=details,
        total=len(details)
    )
