"""
Payment business logic operations.

This module contains all business logic for payment management including
creation, status updates, and integration with payment providers.
"""

import uuid
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, func

from app.models.payment import Payment, PaymentStatus, PaymentProvider
from app.models.order import Order, OrderStatus
from app.models.store import Store
from app.models.tenant import Tenant
from app.schemas.payment import InitializePaymentRequest
from app.libs.database import with_db_session_classmethod


class PaymentOperation:
    """Business logic operations for payment management."""

    @classmethod
    @with_db_session_classmethod
    def initialize_payment(
        cls, 
        db: Session,
        request: InitializePaymentRequest, 
        created_by: Optional[uuid.UUID] = None
    ) -> Payment:
        """
        Initialize a new payment transaction.

        Args:
            request: Payment initialization request
            created_by: ID of user creating the payment

        Returns:
            Created payment transaction instance

        Raises:
            ValueError: If validation fails
            IntegrityError: If database constraints are violated
        """
        # Validate order exists and can be paid
        order = cls._validate_order_for_payment(request.order_id)

        # Validate store and tenant exist
        _ = cls._validate_store_exists(request.store_id)
        _ = cls._validate_tenant_exists(request.tenant_id)

        # Validate amount matches order total
        if request.total_amount != order.total_amount:
            raise ValueError(
                f"Payment amount {request.total_amount} does not match order total {order.total_amount}"
            )

        # Check if order already has an active payment transaction
        existing_payment = (
            db.query(Payment)
            .filter(
                and_(
                    Payment.store_id == request.store_id,
                    Payment.tenant_id == request.tenant_id,
                    Payment.deleted_at.is_(None),
                    Payment.status.in_(
                        [
                            PaymentStatus.NEW,
                            PaymentStatus.WAITING_FOR_PAYMENT_DETAIL,
                            PaymentStatus.WAITING_FOR_PURCHASE,
                        ]
                    ),
                )
            )
            .first()
        )

        if existing_payment:
            raise ValueError(f"Order {request.order_id} already has an active payment transaction")

        # Create payment transaction
        payment_transaction = Payment(
            order_id=request.order_id,
            store_id=request.store_id,
            tenant_id=request.tenant_id,
            total_amount=request.total_amount,
            provider=request.provider,
            status=PaymentStatus.NEW,
            created_by=created_by,
        )

        try:
            db.add(payment_transaction)
            db.flush()  # Get payment transaction ID

            # Update order status to waiting for payment
            order.update_status(OrderStatus.WAITING_FOR_PAYMENT, updated_by=created_by)

            db.commit()
            db.refresh(payment_transaction)
            return payment_transaction

        except Exception as e:
            db.rollback()
            raise e

    @classmethod
    @with_db_session_classmethod
    def get_payment_by_id(cls, db: Session, payment_id: uuid.UUID) -> Optional[Payment]:
        """
        Get payment transaction by ID.

        Args:
            payment_id: Payment transaction ID

        Returns:
            Payment transaction instance or None if not found

        Raises:
            ValueError: If payment transaction not found
        """
        payment_transaction = (
            db.query(Payment)
            .filter(and_(Payment.id == payment_id, Payment.deleted_at.is_(None)))
            .first()
        )
        
        if not payment_transaction:
            raise ValueError(f"Payment transaction with ID {payment_id} not found")
        
        return payment_transaction

    @classmethod
    @with_db_session_classmethod
    def _validate_order_for_payment(cls, db: Session, order_id: uuid.UUID) -> Order:
        """Validate order exists and can be paid."""
        order = (
            db.query(Order)
            .filter(and_(Order.id == order_id, Order.deleted_at.is_(None)))
            .first()
        )

        if not order:
            raise ValueError(f"Order with ID {order_id} not found")

        if not order.can_be_paid:
            raise ValueError(f"Order {order_id} cannot be paid in current status: {order.status.value}")

        return order

    @classmethod
    @with_db_session_classmethod
    def _validate_store_exists(cls, db: Session, store_id: uuid.UUID) -> Store:
        """Validate store exists."""
        store = (
            db.query(Store)
            .filter(and_(Store.id == store_id, Store.deleted_at.is_(None)))
            .first()
        )

        if not store:
            raise ValueError(f"Store with ID {store_id} not found")

        return store

    @classmethod
    @with_db_session_classmethod
    def _validate_tenant_exists(cls, db: Session, tenant_id: uuid.UUID) -> Tenant:
        """Validate tenant exists."""
        tenant = (
            db.query(Tenant)
            .filter(and_(Tenant.id == tenant_id, Tenant.deleted_at.is_(None)))
            .first()
        )

        if not tenant:
            raise ValueError(f"Tenant with ID {tenant_id} not found")

        return tenant
