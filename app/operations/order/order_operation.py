"""
Order business logic operations.

This module contains all business logic for order management including
creation, updates, cancellation, and status management.
"""

import uuid
import json
from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.libs.database import with_db_session_classmethod
from app.models.machine import Machine, MachineStatus, MachineType
from app.models.order import Order, OrderStatus, OrderDetail, OrderDetailStatus
from app.models.store import Store, StoreStatus
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.operations.machine.machine_operation import MachineOperation
from app.schemas.order import CreateOrderRequest, ListOrderQueryParams
from app.libs.database import get_db_session


class OrderOperation:
    """Business logic operations for order management."""

    @classmethod
    @with_db_session_classmethod
    def create_order(
        cls,
        db: Session,
        request: CreateOrderRequest,
        created_by: Optional[uuid.UUID] = None,
    ) -> Order:
        """
        Create a new order with validation and business rules.

        Args:
            request: Order creation request
            created_by: ID of user creating the order

        Returns:
            Created order instance

        Raises:
            ValueError: If validation fails
            IntegrityError: If database constraints are violated
        """
        store = cls._validate_store(request.store_id)

        machine_selections = cls._validate_machine_availability(
            request.machine_selections
        )

        order = Order(
            store_id=request.store_id,
            status=OrderStatus.NEW,
            total_amount=Decimal("0.00"),
            total_washer=0,
            total_dryer=0,
            created_by=created_by,
        )

        try:
            db.add(order)
            db.flush()

            total_amount = Decimal("0.00")
            washer_count = 0
            dryer_count = 0

            for selection in machine_selections:
                machine = (
                    db.query(Machine).filter(Machine.id == selection.machine_id).first()
                )

                # Calculate price based on machine type
                if machine.machine_type == MachineType.WASHER:
                    # For washer: base_price + addons
                    price = machine.base_price
                    if selection.add_ons:
                        add_ons_price = cls._calculate_add_ons_price(selection.add_ons)
                        price += add_ons_price
                elif machine.machine_type == MachineType.DRYER:
                    # For dryer: base_price * DRYING_DURATION_MINUTE * quantity
                    price = machine.base_price
                    if selection.add_ons:
                        # Find DRYING_DURATION_MINUTE add-on
                        drying_duration = cls._get_drying_duration_from_addons(
                            selection.add_ons
                        )
                        if drying_duration > 0:
                            price = machine.base_price * drying_duration
                        else:
                            # If no drying duration specified, use base price
                            price = machine.base_price

                # Serialize add_ons to JSON string if it's a list
                add_ons_json = None
                if selection.add_ons:
                    add_ons_data = []
                    for add_on in selection.add_ons:
                        add_on_dict = add_on.dict()
                        # Convert Decimal to float for JSON serialization
                        if "price" in add_on_dict and isinstance(
                            add_on_dict["price"], Decimal
                        ):
                            add_on_dict["price"] = float(add_on_dict["price"])
                        add_ons_data.append(add_on_dict)

                    add_ons_json = json.dumps(add_ons_data)

                order_detail = OrderDetail(
                    order_id=order.id,
                    machine_id=selection.machine_id,
                    add_ons=add_ons_json,
                    price=price,
                    created_by=created_by,
                )

                db.add(order_detail)

                total_amount += price
                if machine.machine_type == MachineType.WASHER:
                    washer_count += 1
                elif machine.machine_type == MachineType.DRYER:
                    dryer_count += 1

            order.total_amount = total_amount
            order.total_washer = washer_count
            order.total_dryer = dryer_count

            order.status = OrderStatus.NEW

            db.commit()
            db.refresh(order)

            return order

        except Exception as e:
            db.rollback()
            raise e

    @classmethod
    @with_db_session_classmethod
    def get_order_by_id(cls, db: Session, order_id: uuid.UUID) -> Optional[Order]:
        """
        Get order by ID with all details.

        Args:
            order_id: Order ID

        Returns:
            Order instance or None if not found
        """
        order = (
            db.query(
                *Order.__table__.columns,
                Store.name.label("store_name"),
            )
            .join(Store, Order.store_id == Store.id)
            .filter(and_(Order.id == order_id, Order.deleted_at.is_(None)))
            .first()
        )
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")

        return order

    @classmethod
    @with_db_session_classmethod
    def get_orders_by_store(
        cls,
        db: Session,
        store_id: uuid.UUID,
        page: int = 1,
        per_page: int = 20,
        status: Optional[OrderStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get orders for a specific store with pagination and filtering.

        Args:
            store_id: Store ID
            page: Page number (1-based)
            per_page: Items per page
            status: Filter by order status
            start_date: Filter orders from this date
            end_date: Filter orders to this date

        Returns:
            Dictionary with orders and pagination info
        """
        query = db.query(Order).filter(
            and_(Order.store_id == store_id, Order.deleted_at.is_(None))
        )

        # Apply filters
        if status:
            query = query.filter(Order.status == status)

        if start_date:
            query = query.filter(Order.created_at >= start_date)

        if end_date:
            query = query.filter(Order.created_at <= end_date)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        orders = (
            query.order_by(Order.created_at.desc()).offset(offset).limit(per_page).all()
        )

        return {
            "orders": orders,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }

    @classmethod
    @with_db_session_classmethod
    def get_orders_by_tenant(
        cls, db: Session, current_user: User, query_params: ListOrderQueryParams
    ) -> List[Order]:
        """
        Get orders by tenant with pagination and filtering.

        Args:
            tenant_id: Tenant ID
        """
        base_query = (
            db.query(
                *Order.__table__.columns,
                Store.name.label("store_name"),
            )
            .join(Store, Order.store_id == Store.id)
        )

        if query_params.status:
            base_query = base_query.filter(Order.status == query_params.status)

        if query_params.start_date:
            base_query = base_query.filter(Order.created_at >= query_params.start_date)

        if query_params.end_date:
            base_query = base_query.filter(Order.created_at <= query_params.end_date)

        if query_params.store_id:
            base_query = base_query.filter(Order.store_id == query_params.store_id)

        if query_params.tenant_id:
            tenant_member = db.query(TenantMember).filter(
                TenantMember.tenant_id == query_params.tenant_id,
                TenantMember.user_id == current_user.id,
            ).first()
            if not tenant_member:
                raise ValueError("You don't have permission to get this tenant")

            base_query = base_query.filter(
                Store.tenant_id == query_params.tenant_id
            )

        result = (
            base_query
            .order_by(Order.created_at.desc())
            .offset((query_params.page - 1) * query_params.page_size)
            .limit(query_params.page_size)
            .all()
        )
        total = base_query.count()

        return total, result

    @classmethod
    @with_db_session_classmethod
    def update_order_status(
        cls,
        db: Session,
        order_id: uuid.UUID,
        status: OrderStatus,
        updated_by: Optional[uuid.UUID] = None,
    ) -> Order:
        """
        Update order status with validation.

        Args:
            order_id: Order ID
            request: Status update request
            updated_by: ID of user updating the order

        Returns:
            Updated order instance

        Raises:
            ValueError: If order not found or invalid status transition
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")

        order.status = status
        order.updated_by = updated_by

        if status == OrderStatus.IN_PROGRESS:
            cls._start_machines(updated_by, order.id)
        elif status == OrderStatus.FINISHED:
            cls._finish_machines(updated_by, order.id)
        elif status == OrderStatus.CANCELLED:
            cls._cancel_machines(updated_by, order.id)

        db.add(order)
        db.commit()
        return order

    @classmethod
    @with_db_session_classmethod
    def cancel_order(
        cls, db: Session, order_id: uuid.UUID, cancelled_by: Optional[uuid.UUID] = None
    ) -> Order:
        """
        Cancel an order and free up machines.

        Args:
            order_id: Order ID
            cancelled_by: ID of user cancelling the order

        Returns:
            Cancelled order instance

        Raises:
            ValueError: If order cannot be cancelled
        """
        order = cls.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")

        if not order.can_be_cancelled:
            raise ValueError(
                f"Order with status {order.status.value} cannot be cancelled"
            )

        # Update order status
        order.update_status(OrderStatus.CANCELLED, cancelled_by)

        # Cancel all order details and free machines
        cls._cancel_machines(order)

        db.commit()
        return order

    @classmethod
    @with_db_session_classmethod
    def wait_for_payment(
        cls, db: Session, order_id: uuid.UUID, updated_by: Optional[uuid.UUID] = None
    ) -> Order:
        """
        Wait for payment for an order.
        """
        order = (
            db.query(Order)
            .filter(and_(Order.id == order_id, Order.deleted_at.is_(None)))
            .first()
        )
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")

        if not order.can_be_paid:
            raise ValueError(
                f"Order {order_id} cannot be paid in current status: {order.status.value}"
            )

        # Cancel all order details and free machines
        order.update_status(OrderStatus.WAITING_FOR_PAYMENT, updated_by)
        db.commit()
        db.refresh(order)

        return order

    @classmethod
    def calculate_order_total(cls, order_id: uuid.UUID) -> Decimal:
        """
        Calculate total amount for an order.

        Args:
            order_id: Order ID

        Returns:
            Total amount
        """
        order = cls.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")

        return order.calculate_total()

    @classmethod
    @with_db_session_classmethod
    def get_order_statistics(
        cls,
        db: Session,
        store_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get order statistics.

        Args:
            store_id: Filter by store ID
            start_date: Filter from date
            end_date: Filter to date

        Returns:
            Statistics dictionary
        """
        query = db.query(Order).filter(Order.deleted_at.is_(None))

        if store_id:
            query = query.filter(Order.store_id == store_id)

        if start_date:
            query = query.filter(Order.created_at >= start_date)

        if end_date:
            query = query.filter(Order.created_at <= end_date)

        # Basic statistics
        total_orders = query.count()
        total_revenue = query.with_entities(
            func.sum(Order.total_amount)
        ).scalar() or Decimal("0.00")

        # Orders by status
        status_counts = {}
        for status in OrderStatus:
            count = query.filter(Order.status == status).count()
            status_counts[status.value] = count

        # Orders by store
        store_counts = {}
        if not store_id:  # Only if not filtering by specific store
            store_orders = (
                query.with_entities(Order.store_id, func.count(Order.id))
                .group_by(Order.store_id)
                .all()
            )

            for store_id_val, count in store_orders:
                store = db.query(Store).filter(Store.id == store_id_val).first()
                store_name = store.name if store else f"Store {store_id_val}"
                store_counts[store_name] = count

        # Machine usage
        total_washers = query.with_entities(func.sum(Order.total_washer)).scalar() or 0
        total_dryers = query.with_entities(func.sum(Order.total_dryer)).scalar() or 0

        # Average order value
        avg_order_value = (
            total_revenue / total_orders if total_orders > 0 else Decimal("0.00")
        )

        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "orders_by_status": status_counts,
            "orders_by_store": store_counts,
            "average_order_value": avg_order_value,
            "total_washers_booked": total_washers,
            "total_dryers_booked": total_dryers,
        }

    @classmethod
    @with_db_session_classmethod
    def _validate_store(cls, db: Session, store_id: uuid.UUID) -> Store:
        """Validate store exists and is active."""
        store = (
            db.query(Store)
            .filter(
                and_(
                    Store.id == store_id,
                    Store.deleted_at.is_(None),
                    Store.status == StoreStatus.ACTIVE,
                )
            )
            .first()
        )

        if not store:
            raise ValueError(f"Active store with ID {store_id} not found")

        return store

    @classmethod
    @with_db_session_classmethod
    def _validate_machine_availability(
        cls, db: Session, machine_selections: List[Any]
    ) -> List[Any]:
        """Validate machines are available for booking."""
        machine_ids = [selection.machine_id for selection in machine_selections]

        # Check machines exist and are available
        machines = (
            db.query(Machine)
            .filter(
                and_(
                    Machine.id.in_(machine_ids),
                    Machine.deleted_at.is_(None),
                    Machine.status == MachineStatus.IDLE,
                )
            )
            .all()
        )

        if len(machines) != len(machine_ids):
            available_ids = {str(m.id) for m in machines}
            requested_ids = {str(mid) for mid in machine_ids}
            unavailable = requested_ids - available_ids
            raise ValueError(f"Machines not available: {', '.join(unavailable)}")

        return machine_selections

    @classmethod
    @with_db_session_classmethod
    def _calculate_add_ons_price(
        cls, db: Session, add_ons: List[Dict[str, Any]]
    ) -> Decimal:
        """Calculate price for add-ons."""
        total = Decimal("0.00")

        for add_on in add_ons:
            if isinstance(add_on, dict) and "price" in add_on and "quantity" in add_on:
                price = Decimal(str(add_on["price"]))
                quantity = int(add_on["quantity"])
                total += price * quantity

        return total

    @classmethod
    def _get_drying_duration_from_addons(cls, add_ons: List[Any]) -> int:
        """Extract drying duration in minutes from add-ons."""
        from app.models.order import AddOnType

        for add_on in add_ons:
            if isinstance(add_on, dict) and "type" in add_on and "quantity" in add_on:
                if add_on["type"] == AddOnType.DRYING_DURATION_MINUTE.value:
                    return int(add_on["quantity"])
            elif hasattr(add_on, "type") and hasattr(add_on, "quantity"):
                if add_on.type == AddOnType.DRYING_DURATION_MINUTE:
                    return int(add_on.quantity)

        return 0

    @classmethod
    @with_db_session_classmethod
    def _start_machines(cls, db: Session, updated_by: Optional[uuid.UUID], order_id: uuid.UUID) -> None:
        """Start machines for an order."""
        order_details = (
            db.query(OrderDetail).filter(OrderDetail.order_id == order_id).all()
        )

        for order_detail in order_details:
            if order_detail.machine.status == MachineStatus.IDLE:
                MachineOperation.start(
                    user=updated_by,
                    total_amount=order_detail.price,
                    machine_id=order_detail.machine.id
                )
                order_detail.update_status(OrderDetailStatus.IN_PROGRESS)
                db.add(order_detail)

        db.commit()

    @classmethod
    @with_db_session_classmethod
    def _finish_machines(cls, db: Session, updated_by: Optional[uuid.UUID], order_id: uuid.UUID) -> None:
        """Finish machines for an order."""
        order_details = (
            db.query(OrderDetail).filter(OrderDetail.order_id == order_id).all()
        )

        """Finish machines for an order."""
        for order_detail in order_details:
            if order_detail.machine.status == MachineStatus.BUSY:
                MachineOperation.finish(order_detail.machine.id)
                order_detail.update_status(OrderDetailStatus.FINISHED)
                db.add(order_detail)
        db.commit()

    @classmethod
    @with_db_session_classmethod
    def _cancel_machines(cls, db: Session, updated_by: Optional[uuid.UUID], order_id: uuid.UUID) -> None:
        """Cancel machines for an order."""
        order_details = (
            db.query(OrderDetail).filter(OrderDetail.order_id == order_id).all()
        )

        """Cancel machines for an order."""
        for order_detail in order_details:
            if order_detail.machine.status == MachineStatus.BUSY:
                MachineOperation.finish(order_detail.machine.id)
                order_detail.update_status(OrderDetailStatus.CANCELLED)
                db.add(order_detail)
        db.commit()
