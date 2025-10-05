"""
Payment business logic operations.

This module contains all business logic for payment management including
creation, status updates, and integration with payment providers.
"""

import uuid
import random
import string
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.logging import logger
from app.models.payment import Payment, PaymentStatus, PaymentProvider, PaymentMethod
from app.models.order import Order, OrderStatus
from app.models.store import Store
from app.models.tenant import Tenant
from app.schemas.payment import InitializePaymentRequest
from app.libs.database import with_db_session_classmethod
from app.libs.vietqr import GenerateQRCodeRequest
from app.services.payment_service import PaymentService, PaymentProviderEnum
from app.operations.order.order_operation import OrderOperation


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
        order = OrderOperation.wait_for_payment(request.order_id, created_by)
        
        # Validate store and tenant exist
        store = cls._validate_store_exists(request.store_id)
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

        # Get payment method details from store
        payment_method_details = cls._get_payment_method_details_from_store(store, request.payment_method)

        # Generate transaction code if not provided
        transaction_code = getattr(request, 'transaction_code', None)
        if not transaction_code:
            transaction_code = cls._generate_transaction_code()

        # Create payment transaction
        payment_transaction = Payment(
            order_id=request.order_id,
            store_id=request.store_id,
            tenant_id=request.tenant_id,
            total_amount=request.total_amount,
            provider=PaymentProvider.VIET_QR,  # Default provider
            payment_method=request.payment_method,
            payment_method_details=payment_method_details,
            status=PaymentStatus.NEW,
            transaction_code=transaction_code,
            created_by=created_by,
            updated_by=created_by,
        )

        try:
            db.add(payment_transaction)
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
            
            if payment.payment_method == PaymentMethod.QR:
                transaction_id, details = cls._generate_payment_qr_code(payment, order)
            else:
                raise ValueError(f"Payment {payment_id} cannot generate details for payment method {payment.payment_method.value}")

            payment.details = details
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
    def _generate_payment_qr_code(cls, payment: Payment, order: Order):
        """Generate payment QR code."""
        payment_service = PaymentService(provider_name=PaymentProviderEnum.VIETQR)
        
        # Payment method details
        _ = payment.payment_method
        payment_method_details = payment.payment_method_details
        bank_code = payment_method_details.get('bank_code')
        bank_account_number = payment_method_details.get('bank_account_number')
        bank_account_name = payment_method_details.get('bank_account_name')
        
        if not bank_code or not bank_account_number or not bank_account_name:
            raise ValueError("Bank code, bank account number, and bank account name are required")
        
        # Create QR generation request
        qr_request = GenerateQRCodeRequest(
            amount=str(int(payment.total_amount)),
            content=str(order.id),
            orderId=str(order.id),
            terminalCode=str(order.store_id),
            bankCode=bank_code,
            bankAccountNumber=bank_account_number,
            bankAccountName=bank_account_name,
        )
        
        # Generate QR code
        qr_code, transaction_id, transaction_ref_id = payment_service.generate_qr_code(request=qr_request)
        
        # Update payment with generated details
        details = {
            "qr_code": qr_code,
            "transaction_id": transaction_id,
            "transaction_ref_id": transaction_ref_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
        }

        return transaction_id, details

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
    def _get_payment_method_details_from_store(cls, store: Store, payment_method: PaymentMethod) -> Optional[Dict[str, Any]]:
        """
        Get payment method details from store's payment methods.
        
        Args:
            store: Store instance
            payment_method: Payment method to get details for
            
        Returns:
            Payment method details dictionary or None if not found
        """
        if not store.payment_methods:
            raise ValueError(f"Store {store.id} does not have any payment methods")
        
        # Find the payment method in store's payment methods
        for method in store.payment_methods:
            if method.get('payment_method') == payment_method.value:
                return method.get('details')
        
        raise ValueError(f"Payment method {payment_method.value} not found in store {store.id}")

    @classmethod
    @with_db_session_classmethod
    def update_payment_status_by_transaction_code(
        cls,
        db: Session,
        transaction_code: str,
        status: str,
        provider: str = "VIET_QR"
    ) -> Dict[str, Any]:
        """
        Generic method to update payment status by transaction ID.
        
        This method finds a payment by its provider transaction ID and updates
        its status. It's designed to work with any payment provider.
        
        Args:
            transaction_code: Payment provider transaction code
            status: Payment status to update to
            provider: Payment provider name (default: VIET_QR)
            
        Returns:
            Dict containing updated payment information
            
        Raises:
            ValueError: If payment not found or invalid status
        """
        try:
            payment = (
                db.query(Payment)
                .filter(
                    and_(
                        Payment.transaction_code == transaction_code,
                        Payment.deleted_at.is_(None)
                    )
                )
                .first()
            )
            
            if not payment:
                raise ValueError(f"Payment with transaction code {transaction_code} not found")

            try:
                new_status = PaymentStatus(status)
            except ValueError:
                raise ValueError(f"Invalid payment status: {status}")

            order = payment.order
            
            payment.update_status(new_status)
            
            if new_status == PaymentStatus.SUCCESS:
                order.update_status(OrderStatus.PAYMENT_SUCCESS)
                logger.info(f"Payment completed for order {order.id} via {provider} transaction {transaction_code}")
            elif new_status == PaymentStatus.FAILED:
                order.update_status(OrderStatus.PAYMENT_FAILED)
                logger.info(f"Payment failed for order {order.id} via {provider} transaction {transaction_code}")
            elif new_status == PaymentStatus.CANCELLED:
                order.update_status(OrderStatus.CANCELLED)
                logger.info(f"Payment refunded for order {order.id} via {provider} transaction {transaction_code}")
            
            db.add(payment)
            db.add(order)
            db.commit()
            db.refresh(payment)
            
            return {
                "payment_id": str(payment.id),
                "order_id": str(order.id),
                "status": payment.status.value,
                "transaction_code": transaction_code,
                "provider": provider
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating payment status for transaction {transaction_code}: {str(e)}")
            raise e

    @classmethod
    @with_db_session_classmethod
    def _generate_transaction_code(cls, db: Session) -> str:
        """
        Generate a unique 8-character transaction code.
        
        The code contains uppercase letters and digits, with at least one letter and one digit.
        
        Args:
            db: Database session
            
        Returns:
            Unique 8-character transaction code
            
        Raises:
            RuntimeError: If unable to generate unique code after maximum attempts
        """
        max_attempts = 100
        attempts = 0
        
        while attempts < max_attempts:
            # Generate 8 characters with at least one letter and one digit
            letters = string.ascii_uppercase
            digits = string.digits
            
            # Ensure at least one letter and one digit
            code = [
                random.choice(letters),  # At least one letter
                random.choice(digits)    # At least one digit
            ]
            
            # Fill remaining 6 positions randomly
            for _ in range(6):
                code.append(random.choice(letters + digits))
            
            # Shuffle to randomize positions
            random.shuffle(code)
            transaction_code = ''.join(code)
            
            # Check if code is unique
            existing_payment = (
                db.query(Payment)
                .filter(Payment.transaction_code == transaction_code)
                .first()
            )
            
            if not existing_payment:
                return transaction_code
            
            attempts += 1
        
        raise RuntimeError(f"Unable to generate unique transaction code after {max_attempts} attempts")

    @classmethod
    @with_db_session_classmethod
    def get_payment_by_transaction_code(cls, db: Session, transaction_code: str) -> Optional[Payment]:
        """
        Get payment transaction by transaction code.
        
        Args:
            transaction_code: 8-character transaction code
            
        Returns:
            Payment transaction instance or None if not found
            
        Raises:
            ValueError: If payment transaction not found
        """
        # Normalize transaction code (uppercase, strip whitespace)
        transaction_code = transaction_code.strip().upper()
        
        payment_transaction = (
            db.query(Payment)
            .filter(
                and_(
                    Payment.transaction_code == transaction_code,
                    Payment.deleted_at.is_(None)
                )
            )
            .first()
        )
        
        if not payment_transaction:
            raise ValueError(f"Payment transaction with transaction code {transaction_code} not found")
        
        return payment_transaction
