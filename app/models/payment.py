from enum import Enum
import uuid
from typing import Optional
from decimal import Decimal

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Numeric,
    func,
    event,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates, relationship

from app.libs.database import Base


class PaymentStatus(str, Enum):
    NEW = "NEW"
    WAITING_FOR_PAYMENT_DETAIL = "WAITING_FOR_PAYMENT_DETAIL"
    WAITING_FOR_PURCHASE = "WAITING_FOR_PURCHASE"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    
    
class PaymentMethod(str, Enum):
    QR = "QR"
    CARD = "CARD"
    OTHER = "OTHER"


class PaymentProvider(str, Enum):
    VIET_QR = "VIET_QR"


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    
    status = Column(
        SQLEnum(PaymentStatus, name="payment_status", create_type=False),
        nullable=False,
        default=PaymentStatus.NEW,
        index=True
    )
    details = Column(JSON, nullable=True)  # Store QR value and other payment details
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    provider = Column(
        SQLEnum(PaymentProvider, name="payment_provider", create_type=False),
        nullable=False,
        default=PaymentProvider.VIET_QR,
        index=True
    )
    payment_method = Column(
        SQLEnum(PaymentMethod, name="payment_method", create_type=False),
        nullable=False,
        default=PaymentMethod.QR,
        index=True
    )
    payment_method_details = Column(JSON, nullable=True)
    provider_transaction_id = Column(String(255), nullable=True, index=True)
    transaction_code = Column(String(8), index=True, unique=True)

    # Relationships
    order = relationship("Order", back_populates="payments")
    store = relationship("Store", back_populates="payments")
    tenant = relationship("Tenant", back_populates="payments")
    
    @validates('order_id')
    def validate_order_id(self, key: str, order_id) -> uuid.UUID:
        if not order_id:
            raise ValueError("Order ID is required")
        
        if not isinstance(order_id, uuid.UUID):
            try:
                order_id = uuid.UUID(str(order_id))
            except (ValueError, TypeError):
                raise ValueError("Invalid order ID format")
        
        return order_id

    @validates('status')
    def validate_status(self, key: str, status) -> PaymentStatus:
        if not isinstance(status, PaymentStatus):
            try:
                status = PaymentStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status: {status}. Must be one of {[s.value for s in PaymentStatus]}")
        return status
    
    @validates('provider')
    def validate_provider(self, key: str, provider) -> PaymentProvider:
        if not isinstance(provider, PaymentProvider):
            try:
                provider = PaymentProvider(provider)
            except ValueError:
                raise ValueError(f"Invalid provider: {provider}. Must be one of {[p.value for p in PaymentProvider]}")
        return provider

    @validates('payment_method')
    def validate_payment_method(self, key: str, payment_method) -> PaymentMethod:
        if not isinstance(payment_method, PaymentMethod):
            try:
                payment_method = PaymentMethod(payment_method)
            except ValueError:
                raise ValueError(f"Invalid payment method: {payment_method}. Must be one of {[m.value for m in PaymentMethod]}")
        return payment_method

    @validates('total_amount')
    def validate_total_amount(self, key: str, total_amount) -> Decimal:
        if not isinstance(total_amount, (int, float, Decimal)):
            try:
                total_amount = Decimal(str(total_amount))
            except (ValueError, TypeError):
                raise ValueError("Total amount must be a number")
        
        if total_amount <= 0:
            raise ValueError("Total amount must be greater than 0")
        
        return total_amount
    
    @validates('store_id')
    def validate_store_id(self, key: str, store_id) -> uuid.UUID:
        if not store_id:
            raise ValueError("Store ID is required")
        
        if not isinstance(store_id, uuid.UUID):
            try:
                store_id = uuid.UUID(str(store_id))
            except (ValueError, TypeError):
                raise ValueError("Invalid store ID format")
        
        return store_id
    
    @validates('tenant_id')
    def validate_tenant_id(self, key: str, tenant_id) -> uuid.UUID:
        if not tenant_id:
            raise ValueError("Tenant ID is required")
        
        if not isinstance(tenant_id, uuid.UUID):
            try:
                tenant_id = uuid.UUID(str(tenant_id))
            except (ValueError, TypeError):
                raise ValueError("Invalid tenant ID format")
        
        return tenant_id
    
    @validates('provider_transaction_id')
    def validate_provider_transaction_id(self, key: str, provider_transaction_id: Optional[str]) -> Optional[str]:
        if provider_transaction_id is not None:
            provider_transaction_id = provider_transaction_id.strip()
            if not provider_transaction_id:
                return None
            if len(provider_transaction_id) > 255:
                raise ValueError("Provider transaction ID cannot exceed 255 characters")
        return provider_transaction_id
    
    @validates('transaction_code')
    def validate_transaction_code(self, key: str, transaction_code: str) -> str:
        if transaction_code is None:
            raise ValueError("Transaction code is required")
        
        transaction_code = transaction_code.strip().upper()
        if not transaction_code:
            raise ValueError("Transaction code cannot be empty")
        
        # Validate length (exactly 8 characters)
        if len(transaction_code) != 8:
            raise ValueError("Transaction code must be exactly 8 characters long")
        
        # Validate format (only uppercase letters and digits)
        if not transaction_code.isalnum():
            raise ValueError("Transaction code must contain only uppercase letters and digits")
        
        # Ensure it contains at least one letter and one digit
        has_letter = any(c.isalpha() for c in transaction_code)
        has_digit = any(c.isdigit() for c in transaction_code)
        
        if not has_letter:
            raise ValueError("Transaction code must contain at least one letter")
        if not has_digit:
            raise ValueError("Transaction code must contain at least one digit")
        
        return transaction_code
    
    @validates('payment_method_details')
    def validate_payment_method_details(self, key: str, payment_method_details: Optional[dict]) -> Optional[dict]:
        if payment_method_details is not None:
            if not isinstance(payment_method_details, dict):
                raise ValueError("Payment method details must be a dictionary")
            
            # Validate required fields based on payment method
            if self.payment_method == PaymentMethod.QR:
                required_fields = [
                    'bank_code',
                    'bank_name', 
                    'bank_account_number',
                    'bank_account_name',
                ]
                for field in required_fields:
                    if field not in payment_method_details:
                        raise ValueError(f"QR payment method details must have '{field}' field")
                    
                    if not isinstance(payment_method_details[field], str):
                        raise ValueError(f"QR payment method '{field}' must be a string")
                    
                    if not payment_method_details[field].strip():
                        raise ValueError(f"QR payment method '{field}' cannot be empty")
        
        return payment_method_details
    
    @property
    def is_active(self) -> bool:
        return self.deleted_at is None
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    @property
    def is_successful(self) -> bool:
        return self.status == PaymentStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        return self.status == PaymentStatus.FAILED

    @property
    def is_pending(self) -> bool:
        return self.status in [
            PaymentStatus.NEW,
            PaymentStatus.WAITING_FOR_PAYMENT_DETAIL,
            PaymentStatus.WAITING_FOR_PURCHASE
        ]

    @property
    def is_cancelled(self) -> bool:
        return self.status == PaymentStatus.CANCELLED
    
    def soft_delete(self, deleted_by: Optional[uuid.UUID] = None) -> None:
        """Soft delete the payment transaction"""
        self.deleted_at = func.now()
        self.deleted_by = deleted_by
    
    def restore(self) -> None:
        """Restore the payment transaction"""
        self.deleted_at = None
        self.deleted_by = None
    
    def update_status(self, new_status: PaymentStatus, updated_by: Optional[uuid.UUID] = None) -> None:
        """Update payment transaction status with validation"""
        if not self._is_valid_status_transition(self.status, new_status):
            raise ValueError(f"Invalid status transition from {self.status.value} to {new_status.value}")
        
        self.status = new_status
        self.updated_by = updated_by
    
    def _is_valid_status_transition(self, current_status: PaymentStatus, new_status: PaymentStatus) -> bool:
        """Validate status transition"""
        valid_transitions = {
            PaymentStatus.NEW: [
                PaymentStatus.WAITING_FOR_PAYMENT_DETAIL,
                PaymentStatus.CANCELLED
            ],
            PaymentStatus.WAITING_FOR_PAYMENT_DETAIL: [
                PaymentStatus.WAITING_FOR_PAYMENT_DETAIL,
                PaymentStatus.WAITING_FOR_PURCHASE,
                PaymentStatus.FAILED,
                PaymentStatus.CANCELLED
            ],
            PaymentStatus.WAITING_FOR_PURCHASE: [
                PaymentStatus.SUCCESS,
                PaymentStatus.FAILED,
                PaymentStatus.CANCELLED
            ],
            PaymentStatus.SUCCESS: [],  # Cannot transition from success
            PaymentStatus.FAILED: [
                PaymentStatus.NEW  # Allow retry
            ],
            PaymentStatus.CANCELLED: [],  # Cannot transition from cancelled
        }
        return new_status in valid_transitions.get(current_status, [])
    
    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'deleted_by': str(self.deleted_by) if self.deleted_by else None,
            'order_id': str(self.order_id),
            'status': self.status.value,
            'details': self.details,
            'store_id': str(self.store_id),
            'tenant_id': str(self.tenant_id),
            'total_amount': float(self.total_amount) if self.total_amount else 0.0,
            'provider': self.provider.value,
            'payment_method': self.payment_method.value,
            'payment_method_details': self.payment_method_details,
            'provider_transaction_id': self.provider_transaction_id,
            'transaction_code': self.transaction_code,
        }


@event.listens_for(Payment, 'before_update', propagate=True)
def update_payment_timestamp(mapper, connection, target):
    target.updated_at = func.now()
