from enum import Enum
import uuid
from typing import Optional, List
from decimal import Decimal

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Integer,
    Numeric,
    func,
    event,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates, relationship

from app.libs.database import Base


class OrderStatus(str, Enum):
    NEW = "NEW"
    CANCELLED = "CANCELLED"
    WAITING_FOR_PAYMENT = "WAITING_FOR_PAYMENT"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"


class OrderDetailStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"


class AddOnType(str, Enum):
    """Add-on type enum for validation"""
    HOT_WATER = "HOT_WATER"
    COLD_WATER = "COLD_WATER"
    DETERGENT = "DETERGENT"
    SOFTENER = "SOFTENER"
    DRYING_DURATION_MINUTE = "DRYING_DURATION_MINUTE"


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)

    status = Column(
        SQLEnum(OrderStatus, name="order_status", create_type=False),
        nullable=False,
        default=OrderStatus.NEW,
        index=True
    )
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_washer = Column(Integer, nullable=False, default=0)
    total_dryer = Column(Integer, nullable=False, default=0)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False, index=True)

    # Relationships
    store = relationship("Store", back_populates="orders")
    order_details = relationship("OrderDetail", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")

    @validates('status')
    def validate_status(self, key: str, status) -> OrderStatus:
        if not isinstance(status, OrderStatus):
            try:
                status = OrderStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status: {status}. Must be one of {[s.value for s in OrderStatus]}")
        return status

    @validates('total_amount')
    def validate_total_amount(self, key: str, total_amount) -> Decimal:
        if not isinstance(total_amount, (int, float, Decimal)):
            try:
                total_amount = Decimal(str(total_amount))
            except (ValueError, TypeError):
                raise ValueError("Total amount must be a number")
        
        if total_amount < 0:
            raise ValueError("Total amount cannot be negative")
        
        return total_amount

    @validates('total_washer')
    def validate_total_washer(self, key: str, total_washer: int) -> int:
        if not isinstance(total_washer, int):
            try:
                total_washer = int(total_washer)
            except (ValueError, TypeError):
                raise ValueError("Total washer count must be an integer")
        
        if total_washer < 0:
            raise ValueError("Total washer count cannot be negative")
        
        return total_washer

    @validates('total_dryer')
    def validate_total_dryer(self, key: str, total_dryer: int) -> int:
        if not isinstance(total_dryer, int):
            try:
                total_dryer = int(total_dryer)
            except (ValueError, TypeError):
                raise ValueError("Total dryer count must be an integer")
        
        if total_dryer < 0:
            raise ValueError("Total dryer count cannot be negative")
        
        return total_dryer

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

    @property
    def is_active(self) -> bool:
        return self.deleted_at is None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.NEW, OrderStatus.WAITING_FOR_PAYMENT, OrderStatus.PAYMENT_FAILED]

    @property
    def can_be_paid(self) -> bool:
        """Check if order can be paid"""
        return self.status in [OrderStatus.NEW, OrderStatus.WAITING_FOR_PAYMENT]

    @property
    def is_payment_required(self) -> bool:
        """Check if order requires payment"""
        return self.status in [OrderStatus.NEW, OrderStatus.PAYMENT_FAILED]

    def soft_delete(self, deleted_by: Optional[uuid.UUID] = None) -> None:
        """Soft delete the order"""
        self.deleted_at = func.now()
        self.deleted_by = deleted_by
        self.status = OrderStatus.CANCELLED

    def restore(self) -> None:
        """Restore the order"""
        self.deleted_at = None
        self.deleted_by = None

    def update_status(self, new_status: OrderStatus, updated_by: Optional[uuid.UUID] = None) -> None:
        """Update order status with validation"""
        if not self._is_valid_status_transition(self.status, new_status):
            raise ValueError(f"Invalid status transition from {self.status.value} to {new_status.value}")
        
        self.status = new_status
        self.updated_by = updated_by

    def _is_valid_status_transition(self, current_status: OrderStatus, new_status: OrderStatus) -> bool:
        """Validate status transition"""
        valid_transitions = {
            OrderStatus.NEW: [OrderStatus.WAITING_FOR_PAYMENT, OrderStatus.CANCELLED],
            OrderStatus.WAITING_FOR_PAYMENT: [OrderStatus.PAYMENT_SUCCESS, OrderStatus.PAYMENT_FAILED, OrderStatus.CANCELLED],
            OrderStatus.PAYMENT_FAILED: [OrderStatus.WAITING_FOR_PAYMENT, OrderStatus.CANCELLED],
            OrderStatus.PAYMENT_SUCCESS: [OrderStatus.IN_PROGRESS],
            OrderStatus.IN_PROGRESS: [OrderStatus.FINISHED, OrderStatus.CANCELLED],
            OrderStatus.CANCELLED: [],  # Cannot transition from cancelled
            OrderStatus.FINISHED: [],   # Cannot transition from finished
        }
        return new_status in valid_transitions.get(current_status, [])

    def calculate_total(self) -> Decimal:
        """Calculate total amount from order details"""
        total = Decimal('0.00')
        for detail in self.order_details:
            total += detail.price
        return total

    def update_totals(self) -> None:
        """Update washer/dryer counts and total amount"""
        self.total_washer = sum(1 for detail in self.order_details 
                                if detail.machine.machine_type.value == "WASHER")
        self.total_dryer = sum(1 for detail in self.order_details 
                                if detail.machine.machine_type.value == "DRYER")
        self.total_amount = self.calculate_total()

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'deleted_by': str(self.deleted_by) if self.deleted_by else None,
            'status': self.status.value,
            'total_amount': float(self.total_amount) if self.total_amount else 0.0,
            'total_washer': self.total_washer,
            'total_dryer': self.total_dryer,
            'store_id': str(self.store_id),
        }


class OrderDetail(Base):
    __tablename__ = "order_details"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)

    status = Column(
        SQLEnum(OrderDetailStatus, name="order_detail_status", create_type=False),
        nullable=False,
        default=OrderDetailStatus.NEW,
        index=True
    )
    machine_id = Column(UUID(as_uuid=True), ForeignKey('machines.id'), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'), nullable=False, index=True)
    add_ons = Column(String, nullable=True)  # JSON string for add-ons (unlimited)
    price = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Relationships
    machine = relationship("Machine", back_populates="order_details")
    order = relationship("Order", back_populates="order_details")

    @validates('status')
    def validate_status(self, key: str, status) -> OrderDetailStatus:
        if not isinstance(status, OrderDetailStatus):
            try:
                status = OrderDetailStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status: {status}. Must be one of {[s.value for s in OrderDetailStatus]}")
        return status

    @validates('machine_id')
    def validate_machine_id(self, key: str, machine_id) -> uuid.UUID:
        if not machine_id:
            raise ValueError("Machine ID is required")
        
        if not isinstance(machine_id, uuid.UUID):
            try:
                machine_id = uuid.UUID(str(machine_id))
            except (ValueError, TypeError):
                raise ValueError("Invalid machine ID format")
        
        return machine_id

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

    @validates('price')
    def validate_price(self, key: str, price) -> Decimal:
        if not isinstance(price, (int, float, Decimal)):
            try:
                price = Decimal(str(price))
            except (ValueError, TypeError):
                raise ValueError("Price must be a number")
        
        if price < 0:
            raise ValueError("Price cannot be negative")
        
        return price

    @validates('add_ons')
    def validate_add_ons(self, key: str, add_ons) -> Optional[str]:
        if add_ons is None:
            return None
        
        # Handle list input (from Pydantic schema)
        if isinstance(add_ons, list):
            if not add_ons:  # Empty list
                return None
            # Convert list to JSON string
            import json
            return json.dumps(add_ons)
        
        # Handle string input (from database or direct assignment)
        if isinstance(add_ons, str):
            add_ons = add_ons.strip()
            if not add_ons:
                return None
            
            # Basic JSON validation
            import json
            try:
                json.loads(add_ons)
            except json.JSONDecodeError:
                raise ValueError("Add-ons must be valid JSON")
            
            return add_ons
        
        # Handle other types by converting to JSON
        import json
        try:
            return json.dumps(add_ons)
        except (TypeError, ValueError):
            raise ValueError("Add-ons must be serializable to JSON")

    @property
    def is_active(self) -> bool:
        return self.deleted_at is None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def can_be_cancelled(self) -> bool:
        """Check if order detail can be cancelled"""
        return self.status in [OrderDetailStatus.NEW, OrderDetailStatus.IN_PROGRESS]

    def soft_delete(self, deleted_by: Optional[uuid.UUID] = None) -> None:
        """Soft delete the order detail"""
        self.deleted_at = func.now()
        self.deleted_by = deleted_by
        self.status = OrderDetailStatus.CANCELLED

    def restore(self) -> None:
        """Restore the order detail"""
        self.deleted_at = None
        self.deleted_by = None

    def update_status(self, new_status: OrderDetailStatus, updated_by: Optional[uuid.UUID] = None) -> None:
        """Update order detail status with validation"""
        if not self._is_valid_status_transition(self.status, new_status):
            raise ValueError(f"Invalid status transition from {self.status.value} to {new_status.value}")
        
        self.status = new_status
        self.updated_by = updated_by

    def _is_valid_status_transition(self, current_status: OrderDetailStatus, new_status: OrderDetailStatus) -> bool:
        """Validate status transition"""
        valid_transitions = {
            OrderDetailStatus.NEW: [OrderDetailStatus.IN_PROGRESS, OrderDetailStatus.CANCELLED],
            OrderDetailStatus.IN_PROGRESS: [OrderDetailStatus.FINISHED, OrderDetailStatus.CANCELLED],
            OrderDetailStatus.CANCELLED: [],  # Cannot transition from cancelled
            OrderDetailStatus.FINISHED: [],   # Cannot transition from finished
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
            'status': self.status.value,
            'machine_id': str(self.machine_id),
            'order_id': str(self.order_id),
            'add_ons': self.add_ons,
            'price': float(self.price) if self.price else 0.0,
        }


@event.listens_for(Order, 'before_update', propagate=True)
def update_order_timestamp(mapper, connection, target):
    target.updated_at = func.now()


@event.listens_for(OrderDetail, 'before_update', propagate=True)
def update_order_detail_timestamp(mapper, connection, target):
    target.updated_at = func.now()
