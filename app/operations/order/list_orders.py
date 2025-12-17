from typing import List
from sqlalchemy.orm import Session, Query

from app.models.order import Order
from app.models.payment import Payment
from app.models.store import Store
from app.models.store_member import StoreMember
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.schemas.order import ListOrderQueryParams


class ListOrdersOperation:

    def __init__(
        self, 
        db: Session, 
        current_user: User, 
        query_params: ListOrderQueryParams,
    ):
        self.db = db
        self.current_user = current_user
        self.query_params = query_params

    def execute(self) -> tuple[int, List[Order]]:
        base_query = self._build_base_query()

        base_query = self._apply_filters(base_query)
        base_query = self._apply_ordering(base_query)

        total = base_query.count()
        stores = (
            base_query.offset(
                (self.query_params.page - 1) * self.query_params.page_size
            )
            .limit(self.query_params.page_size)
            .all()
        )
        
        return total, stores

    def _build_base_query(self) -> Query:
        base_query = (
            self.db.query(
                *Order.__table__.columns,
                Store.name.label("store_name"),
                Payment.transaction_code.label("transaction_code"),
            )
            .join(Store, Order.store_id == Store.id)
            .join(Payment, Order.id == Payment.order_id)
        )

        if self.current_user.is_tenant_admin:
            tenant_ids_sub_query = (
                self.db.query(TenantMember.tenant_id)
                .filter(TenantMember.user_id == self.current_user.id)
                .subquery()
            )

            base_query = base_query.filter(Store.tenant_id.in_(tenant_ids_sub_query))

        elif self.current_user.is_tenant_staff:
            assigned_store_ids_sub_query = (
                self.db.query(StoreMember.store_id)
                .filter(StoreMember.user_id == self.current_user.id)
                .subquery()
            )
            
            base_query = base_query.filter(Store.id.in_(assigned_store_ids_sub_query))

        return base_query

    def _apply_filters(self, base_query: Query) -> Query:
        if self.query_params.status:
            base_query = base_query.filter(Order.status == self.query_params.status)

        if self.query_params.start_date:
            base_query = base_query.filter(Order.created_at >= self.query_params.start_date)

        if self.query_params.end_date:
            base_query = base_query.filter(Order.created_at <= self.query_params.end_date)

        if self.query_params.store_ids:
            base_query = base_query.filter(Order.store_id.in_(self.query_params.store_ids))

        if self.query_params.payment_status:
            base_query = base_query.filter(Payment.status == self.query_params.payment_status)

        if self.query_params.tenant_id:
            tenant_member = self.db.query(TenantMember).filter(
                TenantMember.tenant_id == self.query_params.tenant_id,
                TenantMember.user_id == self.current_user.id,
            ).first()
            if not tenant_member:
                raise ValueError("You don't have permission to get this tenant")

            base_query = base_query.filter(
                Store.tenant_id == self.query_params.tenant_id
            )
        
        if self.query_params.query:
            base_query = base_query.filter(
                Payment.transaction_code.ilike(f"%{self.query_params.query}%"),
            )
            
        return base_query

    def _apply_ordering(self, base_query: Query) -> Query:
        if self.query_params.order_by:
            if self.query_params.order_direction == "desc":
                base_query = base_query.order_by(getattr(Order, self.query_params.order_by).desc())
            else:
                base_query = base_query.order_by(getattr(Order, self.query_params.order_by).asc())
                
        return base_query
