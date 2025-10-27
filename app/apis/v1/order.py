"""
Order API endpoints.

This module contains all FastAPI endpoints for order management including
CRUD operations, status updates, and order retrieval.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.libs.database import get_db
from app.models.payment import PaymentStatus, PaymentProvider
from app.models.payment import Payment
from app.models.user import User, UserRole
from app.operations.order import OrderOperation
from app.operations.order.order_detail_operation import OrderDetailOperation
from app.operations.order.sync_up_order_operation import SyncUpOrderOperation
from app.schemas.order import (
    CreateOrderRequest,
    OrderResponse,
    ListOrderQueryParams,
    OrderDetailResponse,
    ListOrderDetailQueryParams,
)
from app.schemas.pagination import PaginatedResponse
from app.tasks.payment.payment_tasks import sync_payment_transaction
from app.utils.pagination import get_total_pages

router = APIRouter()


@router.get("/details", response_model=PaginatedResponse[OrderDetailResponse])
async def list_order_details(
    query_params: ListOrderDetailQueryParams = Depends(),
    _: User = Depends(get_current_user)
):
    """
    Get order details.
    """
    try:
        total, order_details = OrderDetailOperation.list(query_params)
        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": order_details,
        }
    except Exception as e:
        logger.error(f"Error getting order details: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


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


@router.get("", response_model=PaginatedResponse[OrderResponse])
async def list_orders(
    query_params: ListOrderQueryParams = Depends(),
    current_user: User = Depends(get_current_user)
):
    try:
        total, orders = OrderOperation.get_orders_by_tenant(
            current_user,
            query_params
        )

        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": orders,
        }
    except Exception as e:
        logger.error("List orders failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{order_id}/trigger-payment-success")
async def test_trigger_payment_success(
    order_id: uuid.UUID = Path(..., description="Order ID"),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test trigger payment success.
    """
    try:
        payment = db.query(Payment).filter(Payment.order_id == order_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        sync_payment_transaction(
            content=payment.transaction_code,
            status=PaymentStatus.SUCCESS,
            provider=PaymentProvider.VIET_QR
        )

        return { "success": True }
    except Exception as e:
        logger.error(f"Error triggering payment success: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{order_id}/trigger-payment-timeout")
async def test_trigger_payment_timeout(
    order_id: uuid.UUID = Path(..., description="Order ID"),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test trigger payment timeout.
    """
    try:
        payment = db.query(Payment).filter(Payment.order_id == order_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        sync_payment_transaction(
            content=payment.transaction_code,
            status=PaymentStatus.CANCELLED,
            provider=PaymentProvider.VIET_QR
        )

        return { "success": True }
    except Exception as e:
        logger.error(f"Error triggering payment timeout: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{order_id}/sync-up")
async def sync_up_order(
    order_id: uuid.UUID = Path(..., description="Order ID"),
    current_user: User = Depends(get_current_user),
):
    """
    Sync up order.
    """
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        SyncUpOrderOperation.execute(order_id)
        return { "success": True }
    except Exception as e:
        logger.error(f"Error syncing up order: {str(e)}")
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
