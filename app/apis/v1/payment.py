"""
Payment API endpoints.

This module contains all FastAPI endpoints for payment management including
creation, status updates, and integration with orders.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.dialects.postgresql.psycopg import logger
from sqlalchemy.orm import Session

from app.apis.deps import get_current_user
from app.libs.database import get_db
from app.models.user import User
from app.operations.payment import PaymentOperation
from app.tasks.payment.payment_tasks import generate_payment_details
from app.schemas.payment import (
    InitializePaymentRequest,
    PaymentResponse,
)


router = APIRouter()


@router.post("", response_model=PaymentResponse, status_code=201)
async def initialize_payment(
    request: InitializePaymentRequest,
    user: User = Depends(get_current_user)
):
    """
    Initialize a new payment.
    
    This endpoint creates a new payment for the specified order.
    The payment will be created with NEW status.
    """
    try:
        payment = PaymentOperation.initialize_payment(request, user.id)
        generate_payment_details(str(payment.id))
        return payment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: uuid.UUID = Path(..., description="Payment ID"),
    _: User = Depends(get_current_user)
):
    """
    Get payment by ID.
    
    Returns the payment details including status and transaction information.
    """
    try:
        payment = PaymentOperation.get_payment_by_id(payment_id)
        
        return payment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{payment_id}/test-trigger-payment-success")
async def test_trigger_payment_success(
    payment_id: uuid.UUID = Path(..., description="Payment ID"),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test trigger payment success.
    """
    try:
        from app.models.payment import Payment, PaymentStatus
        
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        payment.update_status(PaymentStatus.SUCCESS)
        db.commit()
        db.refresh(payment)

        return payment
    except Exception as e:
        logger.error(f"Error triggering payment success: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
