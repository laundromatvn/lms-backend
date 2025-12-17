import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.libs.database import get_db
from app.models.payment import PaymentStatus, PaymentProvider
from app.models.payment import Payment
from app.models.order import Order
from app.models.user import User, UserRole
from app.operations.order import OrderOperation
from app.operations.order.list_orders import ListOrdersOperation
from app.operations.order.order_detail_operation import OrderDetailOperation
from app.operations.order.sync_up_order_operation import SyncUpOrderOperation
from app.operations.promotion.check_and_apply_promotion_operation import CheckAndApplyPromotionOperation
from app.schemas.order import (
    CreateOrderRequest,
    OrderResponse,
    ListOrderQueryParams,
    OrderDetailResponse,
    ListOrderDetailQueryParams,
)
from app.schemas.pagination import PaginatedResponse
from app.operations.payment.payment_operation import PaymentOperation
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
    store_ids: list[uuid.UUID] = Query(None, description="List of store IDs to filter orders"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        query_params.store_ids = store_ids
        
        operation = ListOrdersOperation(db, current_user, query_params)
        total, orders = operation.execute()

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
    For testing purposes, this endpoint will reset payment to WAITING_FOR_PURCHASE if it's in a terminal state.
    """
    try:
        payment = db.query(Payment).filter(Payment.order_id == order_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        # For test endpoints, reset payment to WAITING_FOR_PURCHASE if it's in a terminal state
        # This allows testing transitions from any state
        if payment.status in [PaymentStatus.SUCCESS, PaymentStatus.FAILED, PaymentStatus.CANCELLED]:
            payment.status = PaymentStatus.WAITING_FOR_PURCHASE
            db.add(payment)
            db.commit()
            db.refresh(payment)

        # Call the operation directly to ensure synchronous execution and proper commits
        result = PaymentOperation.update_payment_status_by_transaction_code(
            transaction_code=payment.transaction_code,
            status=PaymentStatus.SUCCESS.value,
            provider=PaymentProvider.VIET_QR.value
        )
        
        # Refresh the order to get updated status
        db.expire_all()  # Expire all objects to force fresh query
        order = db.query(Order).filter(Order.id == order_id).first()
        
        return { 
            "success": True,
            "order_status": order.status.value if order else None,
            "payment_status": result.get("status")
        }
    except Exception as e:
        logger.error(f"Error triggering payment success: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{order_id}/trigger-payment-failed")
async def test_trigger_payment_failed(
    order_id: uuid.UUID = Path(..., description="Order ID"),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test trigger payment failed.
    For testing purposes, this endpoint will reset payment to WAITING_FOR_PURCHASE if it's in a terminal state.
    """
    try:
        payment = db.query(Payment).filter(Payment.order_id == order_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        # For test endpoints, reset payment to WAITING_FOR_PURCHASE if it's in a terminal state
        # This allows testing transitions from any state
        if payment.status in [PaymentStatus.SUCCESS, PaymentStatus.FAILED, PaymentStatus.CANCELLED]:
            payment.status = PaymentStatus.WAITING_FOR_PURCHASE
            db.add(payment)
            db.commit()
            db.refresh(payment)

        # Call the operation directly to ensure synchronous execution and proper commits
        result = PaymentOperation.update_payment_status_by_transaction_code(
            transaction_code=payment.transaction_code,
            status=PaymentStatus.FAILED.value,
            provider=PaymentProvider.VIET_QR.value
        )
        
        # Refresh the order to get updated status
        db.expire_all()  # Expire all objects to force fresh query
        order = db.query(Order).filter(Order.id == order_id).first()
        
        return { 
            "success": True,
            "order_status": order.status.value if order else None,
            "payment_status": result.get("status")
        }
    except Exception as e:
        logger.error(f"Error triggering payment failed: {str(e)}")
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

        # Call the operation directly to ensure synchronous execution and proper commits
        result = PaymentOperation.update_payment_status_by_transaction_code(
            transaction_code=payment.transaction_code,
            status=PaymentStatus.CANCELLED.value,
            provider=PaymentProvider.VIET_QR.value
        )
        
        # Refresh the order to get updated status
        db.expire_all()  # Expire all objects to force fresh query
        order = db.query(Order).filter(Order.id == order_id).first()
        
        return { 
            "success": True,
            "order_status": order.status.value if order else None,
            "payment_status": result.get("status")
        }
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


@router.post("/{order_id}/check-promotion", response_model=OrderResponse)
async def check_promotion(
    order_id: uuid.UUID = Path(..., description="Order ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check and apply promotion to an order.
    
    This endpoint checks for applicable promotions and applies the best one to the order.
    Returns the final order with promotion details (sub_total, discount_amount, promotion_summary, total_amount).
    """
    try:
        order = OrderOperation.get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Merge order into current session if it came from a different session
        order = db.merge(order)
        
        order = CheckAndApplyPromotionOperation.execute(order, db=db)
        
        db.commit()
        db.refresh(order)
        
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking promotion: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID = Path(..., description="Order ID"),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get order by ID.
    
    Returns the order with all its details including promotion information (sub_total, discount_amount, promotion_summary, total_amount).
    """
    try:
        order = OrderOperation.get_order_by_id(order_id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting order: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
