"""
Payment business logic operations.

This module contains all business logic for payment management including
creation, status updates, and integration with payment providers.
"""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.logging import logger
from app.models import payment
from app.models.payment import Payment, PaymentStatus, PaymentProvider
from app.models.order import Order, OrderStatus
from app.models.store import Store
from app.models.tenant import Tenant
from app.schemas.payment import InitializePaymentRequest
from app.libs.database import with_db_session_classmethod
from app.libs.vietqr import GenerateQRCodeRequest
from app.services.payment_service import PaymentService, PaymentProviderEnum


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
                    Payment.order_id == request.order_id,
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
            provider=PaymentProvider.VIET_QR,  # Default provider
            payment_method=request.payment_method,
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
    def generate_payment_details(cls, db: Session, payment_id: uuid.UUID) -> Payment:
        """
        Generate payment details including QR code and transaction information.
        
        Args:
            payment_id: Payment transaction ID
            
        Returns:
            Updated payment transaction with generated details
            
        Raises:
            ValueError: If payment not found or invalid status
        """
        payment = cls.get_payment_by_id(payment_id)
        order = cls._validate_order_for_payment(payment.order_id)
        
        # Validate payment can have details generated
        if payment.status != PaymentStatus.NEW:
            raise ValueError(f"Payment {payment_id} cannot generate details in status {payment.status.value}")
        
        try:
            # Update status to waiting for payment detail
            payment.update_status(PaymentStatus.WAITING_FOR_PAYMENT_DETAIL)
            db.commit()
            
            # Generate QR code using payment service
            payment_service = PaymentService(provider_name=PaymentProviderEnum.VIETQR)
            
            # Create QR generation request
            qr_request = GenerateQRCodeRequest(
                amount=str(int(payment.total_amount)),
                content=str(order.id),
                orderId=str(order.id),
                terminalCode=str(order.store_id)
            )
            
            # Generate QR code
            qr_code, transaction_id, transaction_ref_id = payment_service.generate_qr_code(request=qr_request)
            
            # Update payment with generated details
            payment.details = {
                "qr_code": qr_code,
                "transaction_id": transaction_id,
                "transaction_ref_id": transaction_ref_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
            }
            payment.provider_transaction_id = transaction_id
            payment.update_status(PaymentStatus.WAITING_FOR_PURCHASE)

            db.add(payment)
            db.commit()
            db.refresh(payment)
            
            return payment
            
        except Exception as e:
            # Update payment status to failed on error
            payment.update_status(PaymentStatus.FAILED)
            db.commit()
            raise e

    @classmethod
    @with_db_session_classmethod
    def generate_payment_qr_code(cls, db: Session, payment_id: uuid.UUID):
        """Generate payment QR code."""
        payment_service = PaymentService(provider_name=PaymentProviderEnum.VIETQR)
        qr_code, transaction_id, transaction_ref_id = payment_service.generate_qr_code(payment_id)
        payment.details = {
            "qr_code": qr_code,
            "transaction_id": transaction_id,
            "transaction_ref_id": transaction_ref_id
        }
        payment.status = PaymentStatus.WAITING_FOR_PURCHASE
        db.commit()
        db.refresh(payment)
        return payment

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

    @classmethod
    @with_db_session_classmethod
    def update_payment_status_by_transaction_id(
        cls,
        db: Session,
        transaction_id: str,
        status: str,
        provider: str = "VIET_QR"
    ) -> Dict[str, Any]:
        """
        Generic method to update payment status by transaction ID.
        
        This method finds a payment by its provider transaction ID and updates
        its status. It's designed to work with any payment provider.
        
        Args:
            transaction_id: Payment provider transaction ID
            status: Payment status to update to
            provider: Payment provider name (default: VIET_QR)
            
        Returns:
            Dict containing updated payment information
            
        Raises:
            ValueError: If payment not found or invalid status
        """
        try:
            # Find payment by provider transaction ID
            payment = (
                db.query(Payment)
                .filter(
                    and_(
                        Payment.provider_transaction_id == transaction_id,
                        Payment.deleted_at.is_(None)
                    )
                )
                .first()
            )
            
            if not payment:
                raise ValueError(f"Payment with transaction ID {transaction_id} not found")
            
            # Validate status
            try:
                new_status = PaymentStatus(status)
            except ValueError:
                raise ValueError(f"Invalid payment status: {status}")
            
            # Get the order for status updates
            order = payment.order
            
            # Update payment status
            old_status = payment.status
            payment.update_status(new_status)
            
            # Update order status based on payment status
            if new_status == PaymentStatus.COMPLETED:
                order.update_status(OrderStatus.PAID)
                logger.info(f"Payment completed for order {order.id} via {provider} transaction {transaction_id}")
            elif new_status == PaymentStatus.FAILED:
                order.update_status(OrderStatus.PAYMENT_FAILED)
                logger.info(f"Payment failed for order {order.id} via {provider} transaction {transaction_id}")
            elif new_status == PaymentStatus.REFUNDED:
                order.update_status(OrderStatus.REFUNDED)
                logger.info(f"Payment refunded for order {order.id} via {provider} transaction {transaction_id}")
            
            # Update payment details with sync information
            if not payment.details:
                payment.details = {}
            
            payment.details.update({
                f"{provider.lower()}_status_update": {
                    "status": status,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "previous_status": old_status.value
                }
            })
            
            db.add(payment)
            db.add(order)
            db.commit()
            db.refresh(payment)
            
            return {
                "payment_id": str(payment.id),
                "order_id": str(order.id),
                "status": payment.status.value,
                "transaction_id": transaction_id,
                "provider": provider
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating payment status for transaction {transaction_id}: {str(e)}")
            raise e
