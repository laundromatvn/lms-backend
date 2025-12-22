"""
Order detail business logic operations.

This module contains all business logic for order detail management including
creation, updates, and status management for individual machine bookings.
"""

import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, func

from app.models.order import Order, OrderStatus, OrderDetail, OrderDetailStatus
from app.models.machine import Machine, MachineStatus, MachineType
from app.schemas.order import (
    CreateOrderDetailRequest,
    UpdateOrderDetailStatusRequest,
    ListOrderDetailQueryParams,
)
from app.libs.database import with_db_session_classmethod
from app.libs.database import get_db_session


class OrderDetailOperation:
    """Business logic operations for order detail management."""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize order detail operation with database session."""
        self.db_session = db_session or get_db_session()

    @classmethod
    @with_db_session_classmethod
    def list(
        cls, db: Session, query_params: ListOrderDetailQueryParams
    ) -> tuple[int, List[OrderDetail]]:
        base_query = db.query(
            *OrderDetail.__table__.columns,
            Machine.name.label("machine_name"),
            Machine.machine_type.label("machine_type"),
            Machine.relay_no.label("machine_relay_no"),
        ).join(Machine, OrderDetail.machine_id == Machine.id)

        if query_params.order_id:
            base_query = base_query.filter(
                OrderDetail.order_id == query_params.order_id
            )

        total = base_query.count()
        order_details = (
            base_query.order_by(OrderDetail.created_at.desc())
            .offset((query_params.page - 1) * query_params.page_size)
            .limit(query_params.page_size)
            .all()
        )

        return total, order_details

    def create_order_detail(
        self,
        order_id: uuid.UUID,
        request: CreateOrderDetailRequest,
        created_by: Optional[uuid.UUID] = None,
    ) -> OrderDetail:
        """
        Create a new order detail for an existing order.

        Args:
            order_id: Order ID
            request: Order detail creation request
            created_by: ID of user creating the order detail

        Returns:
            Created order detail instance

        Raises:
            ValueError: If validation fails
            IntegrityError: If database constraints are violated
        """
        # Validate order exists and can be modified
        order = self._validate_order_for_modification(order_id)

        # Validate machine is available
        machine = self._validate_machine_availability(request.machine_id)

        # Check if machine is already in this order
        existing_detail = (
            self.db_session.query(OrderDetail)
            .filter(
                OrderDetail.order_id == order_id,
                OrderDetail.machine_id == request.machine_id,
                OrderDetail.deleted_at.is_(None),
            )
            .first()
        )

        if existing_detail:
            raise ValueError(
                f"Machine {request.machine_id} is already booked in this order"
            )

        # Calculate price from machine base price and add-ons
        price = machine.base_price

        # Add add-ons price if any
        if request.add_ons:
            add_ons_price = self._calculate_add_ons_price(request.add_ons)
            price += add_ons_price

        # Create order detail
        order_detail = OrderDetail(
            order_id=order_id,
            machine_id=request.machine_id,
            add_ons=request.add_ons,
            price=price,
            created_by=created_by,
        )

        try:
            self.db_session.add(order_detail)
            self.db_session.flush()

            # Update order totals
            self._update_order_totals(order)

            self.db_session.commit()
            return order_detail

        except Exception as e:
            self.db_session.rollback()
            raise e

    def get_order_detail_by_id(self, detail_id: uuid.UUID) -> Optional[OrderDetail]:
        """
        Get order detail by ID.

        Args:
            detail_id: Order detail ID

        Returns:
            Order detail instance or None if not found
        """
        return (
            self.db_session.query(OrderDetail)
            .filter(and_(OrderDetail.id == detail_id, OrderDetail.deleted_at.is_(None)))
            .first()
        )

    def get_order_details_by_order(self, order_id: uuid.UUID) -> List[OrderDetail]:
        """
        Get all order details for an order.

        Args:
            order_id: Order ID

        Returns:
            List of order detail instances
        """
        return (
            self.db_session.query(OrderDetail)
            .filter(
                and_(OrderDetail.order_id == order_id, OrderDetail.deleted_at.is_(None))
            )
            .all()
        )

    def update_order_detail_status(
        self,
        detail_id: uuid.UUID,
        request: UpdateOrderDetailStatusRequest,
        updated_by: Optional[uuid.UUID] = None,
    ) -> OrderDetail:
        """
        Update order detail status with validation.

        Args:
            detail_id: Order detail ID
            request: Status update request
            updated_by: ID of user updating the order detail

        Returns:
            Updated order detail instance

        Raises:
            ValueError: If order detail not found or invalid status transition
        """
        order_detail = self.get_order_detail_by_id(detail_id)
        if not order_detail:
            raise ValueError(f"Order detail with ID {detail_id} not found")

        # Update status with validation
        order_detail.update_status(request.status, updated_by)

        # Handle status-specific logic
        if request.status == OrderDetailStatus.IN_PROGRESS:
            self._start_machine(order_detail)
        elif request.status == OrderDetailStatus.FINISHED:
            self._finish_machine(order_detail)
        elif request.status == OrderDetailStatus.CANCELLED:
            self._cancel_machine(order_detail)

        self.db_session.commit()
        return order_detail

    def cancel_order_detail(
        self, detail_id: uuid.UUID, cancelled_by: Optional[uuid.UUID] = None
    ) -> OrderDetail:
        """
        Cancel an order detail.

        Args:
            detail_id: Order detail ID
            cancelled_by: ID of user cancelling the order detail

        Returns:
            Cancelled order detail instance

        Raises:
            ValueError: If order detail cannot be cancelled
        """
        order_detail = self.get_order_detail_by_id(detail_id)
        if not order_detail:
            raise ValueError(f"Order detail with ID {detail_id} not found")

        # Check if order can be modified
        order = order_detail.order
        if not self._can_modify_order(order):
            raise ValueError(
                f"Order with status {order.status.value} cannot be modified"
            )

        # Free up machine if it's in progress
        if order_detail.machine.status == MachineStatus.BUSY:
            order_detail.machine.finish_operation()

        # Cancel the order detail
        order_detail.soft_delete(cancelled_by)

        # Update order totals
        self._update_order_totals(order)

        self.db_session.commit()
        return order_detail

    def get_machine_usage_history(
        self, machine_id: uuid.UUID, limit: int = 50
    ) -> List[OrderDetail]:
        """
        Get usage history for a machine.

        Args:
            machine_id: Machine ID
            limit: Maximum number of records to return

        Returns:
            List of order detail instances
        """
        return (
            self.db_session.query(OrderDetail)
            .filter(
                and_(
                    OrderDetail.machine_id == machine_id,
                    OrderDetail.deleted_at.is_(None),
                )
            )
            .order_by(OrderDetail.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_machine_availability_status(self, machine_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get current availability status of a machine.

        Args:
            machine_id: Machine ID

        Returns:
            Dictionary with machine availability information
        """
        machine = (
            self.db_session.query(Machine)
            .filter(and_(Machine.id == machine_id, Machine.deleted_at.is_(None)))
            .first()
        )

        if not machine:
            return {"available": False, "reason": "Machine not found"}

        # Check if machine is currently booked
        active_detail = (
            self.db_session.query(OrderDetail)
            .filter(
                and_(
                    OrderDetail.machine_id == machine_id,
                    OrderDetail.deleted_at.is_(None),
                    OrderDetail.status.in_(
                        [OrderDetailStatus.NEW, OrderDetailStatus.IN_PROGRESS]
                    ),
                )
            )
            .first()
        )

        if active_detail:
            return {
                "available": False,
                "reason": "Machine is currently booked",
                "order_id": str(active_detail.order_id),
                "status": active_detail.status.value,
            }

        return {
            "available": machine.status == MachineStatus.IDLE,
            "reason": (
                "Machine is available"
                if machine.status == MachineStatus.IDLE
                else f"Machine status: {machine.status.value}"
            ),
            "machine_status": machine.status.value,
            "base_price": float(machine.base_price),
        }

    def _validate_order_for_modification(self, order_id: uuid.UUID) -> Order:
        """Validate order exists and can be modified."""
        order = (
            self.db_session.query(Order)
            .filter(and_(Order.id == order_id, Order.deleted_at.is_(None)))
            .first()
        )

        if not order:
            raise ValueError(f"Order with ID {order_id} not found")

        if not self._can_modify_order(order):
            raise ValueError(
                f"Order with status {order.status.value} cannot be modified"
            )

        return order

    def _can_modify_order(self, order: Order) -> bool:
        """Check if order can be modified."""
        return order.status in [
            OrderStatus.NEW,
            OrderStatus.WAITING_FOR_PAYMENT,
            OrderStatus.PAYMENT_FAILED,
        ]

    def _validate_machine_availability(self, machine_id: uuid.UUID) -> Machine:
        """Validate machine exists and is available."""
        machine = (
            self.db_session.query(Machine)
            .filter(
                and_(
                    Machine.id == machine_id,
                    Machine.deleted_at.is_(None),
                    Machine.status == MachineStatus.IDLE,
                )
            )
            .first()
        )

        if not machine:
            raise ValueError(f"Available machine with ID {machine_id} not found")

        return machine

    def _calculate_add_ons_price(self, add_ons: List[Dict[str, Any]]) -> Decimal:
        """Calculate price for add-ons."""
        total = Decimal("0.00")

        for add_on in add_ons:
            if isinstance(add_on, dict) and "price" in add_on and "quantity" in add_on:
                price = Decimal(str(add_on["price"]))
                quantity = int(add_on["quantity"])
                total += price * quantity

        return total

    def _update_order_totals(self, order: Order) -> None:
        """Update order totals based on order details."""
        order_details = self.get_order_details_by_order(order.id)

        total_amount = Decimal("0.00")
        washer_count = 0
        dryer_count = 0

        for detail in order_details:
            total_amount += detail.price

            if detail.machine.machine_type == MachineType.WASHER:
                washer_count += 1
            elif detail.machine.machine_type == MachineType.DRYER:
                dryer_count += 1

        order.total_amount = total_amount
        order.total_washer = washer_count
        order.total_dryer = dryer_count

    def _start_machine(self, order_detail: OrderDetail) -> None:
        """Start machine for an order detail."""
        if order_detail.machine.status == MachineStatus.IDLE:
            order_detail.machine.start()

    def _finish_machine(self, order_detail: OrderDetail) -> None:
        """Finish machine for an order detail."""
        if order_detail.machine.status == MachineStatus.BUSY:
            order_detail.machine.finish_operation()

    def _cancel_machine(self, order_detail: OrderDetail) -> None:
        """Cancel machine for an order detail."""
        if order_detail.machine.status == MachineStatus.BUSY:
            order_detail.machine.finish_operation()
