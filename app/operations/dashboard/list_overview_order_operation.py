from uuid import UUID
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.libs.database import with_db_session_classmethod
from app.models.order import Order
from app.models.payment import Payment
from app.models.payment import PaymentStatus
from app.schemas.dashboard.overview import ListOverviewOrdersQueryParams
from app.models.user import User
from app.models.tenant_member import TenantMember
from app.models.store import Store

class ListOverviewOrderOperation:

    @classmethod
    @with_db_session_classmethod
    def execute(cls, db: Session, current_user: User, query_params: ListOverviewOrdersQueryParams) -> tuple[int, list[Order]]:
        base_query = (
            db.query(
                Order,
                Payment.status.label("payment_status"),
                Payment.transaction_code.label("transaction_code"),
                Payment.payment_method.label("payment_method"),
            )
            .join(Payment, Order.id == Payment.order_id)
            .filter(Payment.status == PaymentStatus.SUCCESS)
        )
        
        if not current_user.is_admin:
            tenant_members = db.query(TenantMember).filter(TenantMember.user_id == current_user.id).all()
            tenant_ids = [tenant_member.tenant_id for tenant_member in tenant_members]
            base_query = (
                base_query
                .join(Store, Order.store_id == Store.id)
                .filter(Store.tenant_id.in_(tenant_ids))
            )

        if query_params.status:
            base_query = base_query.filter(Order.status == query_params.status)

        if query_params.start_date:
            base_query = base_query.filter(Order.created_at >= query_params.start_date)

        if query_params.end_date:
            base_query = base_query.filter(Order.created_at <= query_params.end_date)

        if query_params.store_id:
            base_query = base_query.filter(Order.store_id == query_params.store_id)
            
        if query_params.payment_status:
            base_query = base_query.filter(Payment.status == query_params.payment_status)
            
        if query_params.query:
            base_query = base_query.filter(
                Payment.transaction_code.ilike(f"%{query_params.query}%"),
            )

        if query_params.order_by:
            if query_params.order_direction == "desc":
                base_query = base_query.order_by(getattr(Order, query_params.order_by).desc())
            else:
                base_query = base_query.order_by(getattr(Order, query_params.order_by).asc())

        total = base_query.count()
        result = (
            base_query
            .order_by(Order.created_at.desc())
            .offset((query_params.page - 1) * query_params.page_size)
            .limit(query_params.page_size)
            .all()
        )

        return total, result


