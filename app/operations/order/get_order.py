from uuid import UUID
from sqlalchemy.orm import Session, Query

from app.models.order import Order
from app.models.payment import Payment
from app.models.store import Store
from app.models.store_member import StoreMember
from app.models.tenant_member import TenantMember
from app.models.user import User


class GetOrderOperation:

    def __init__(
        self,
        db: Session,
        current_user: User,
        order_id: UUID,
    ):
        self.db = db
        self.current_user = current_user
        self.order_id = order_id

    def execute(self) -> Order:
        base_query = self._build_base_query()
        order = base_query.first()
        if not order:
            raise ValueError(f"Order with ID {self.order_id} not found")
        return order

    def _build_base_query(self) -> Query:
        return (
            self.db.query(
                *Order.__table__.columns,
                Store.name.label("store_name"),
                Payment.transaction_code.label("transaction_code"),
            )
            .join(Payment, Order.id == Payment.order_id)
            .join(Store, Order.store_id == Store.id)
            .filter(
                Order.id == self.order_id,
                Order.deleted_at.is_(None),
                Payment.deleted_at.is_(None),
                Store.deleted_at.is_(None),
            )
        )

    def _validate(self):
        if self.current_user.is_admin:
            return

        if self.current_user.is_tenant_admin:
            store_ids_sub_query = (
                self.db.query(Store.id)
                .join(TenantMember, Store.tenant_id == TenantMember.tenant_id)
                .filter(
                    TenantMember.user_id == self.current_user.id,
                )
                .subquery()
            )

            is_exists = (
                self.db.query(Order)
                .filter(
                    Order.store_id.in_(store_ids_sub_query),
                    Order.deleted_at.is_(None),
                    Payment.deleted_at.is_(None),
                    Store.deleted_at.is_(None),
                )
                .first()
                is not None
            )

            if not is_exists:
                raise PermissionError("You are not allowed to get this order")

        if self.current_user.is_tenant_staff:
            store_ids_sub_query = (
                self.db.query(StoreMember.store_id)
                .filter(StoreMember.user_id == self.current_user.id)
                .subquery()
            )

            is_exists = (
                self.db.query(Order)
                .filter(Order.store_id.in_(store_ids_sub_query),
                    Order.deleted_at.is_(None),
                    Payment.deleted_at.is_(None),
                    Store.deleted_at.is_(None),
                )
                .first()
                is not None
            )
            
            if not is_exists:
                raise PermissionError("You are not allowed to get this order")

        raise PermissionError("You are not allowed to get this order")
