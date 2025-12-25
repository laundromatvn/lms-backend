from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session, Query

from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.user import User, UserRole
from app.schemas.tenant_member import ListTenantMemberQueryParams


class ListTenantMembersOperation:

    def __init__(
        self, db: Session, current_user: User, query_params: ListTenantMemberQueryParams
    ):
        self.db = db
        self.current_user = current_user
        self.query_params = query_params

    def execute(self) -> None:
        base_query = self._build_base_query()

        base_query = self._apply_filters(base_query)
        base_query = self._apply_ordering(base_query)

        total = base_query.count()
        tenant_members = self._apply_pagination(base_query).all()

        return total, tenant_members

    def _build_base_query(self) -> Query:
        base_query = (
            self.db.query(
                *TenantMember.__table__.columns,
                User.email.label("user_email"),
                User.phone.label("user_phone"),
                User.role.label("user_role"),
                User.status.label("user_status"),
                Tenant.name.label("tenant_name"),
            )
            .join(User, TenantMember.user_id == User.id)
            .join(Tenant, TenantMember.tenant_id == Tenant.id)
        )

        if not self.current_user.is_admin:
            tenant_ids_subquery = (
                self.db.query(TenantMember.tenant_id)
                .filter(TenantMember.user_id == self.current_user.id)
                .subquery()
            )

            base_query = base_query.filter(
                Tenant.id.in_(tenant_ids_subquery)
            )

        return base_query

    def _apply_filters(self, base_query: Query) -> Query:
        if self.query_params.tenant_id:
            base_query = base_query.filter(
                TenantMember.tenant_id == self.query_params.tenant_id
            )

        if self.query_params.search:
            base_query = base_query.filter(
                or_(
                    User.email.ilike(f"%{self.query_params.search}%"),
                    User.phone.ilike(f"%{self.query_params.search}%"),
                )
            )

        return base_query

    def _apply_ordering(self, base_query: Query) -> Query:
        if self.query_params.order_by.startswith("user_"):
            if self.query_params.order_direction == "desc":
                base_query = base_query.order_by(User.email.desc(), User.phone.desc())
            else:
                base_query = base_query.order_by(User.email.asc(), User.phone.asc())

        return base_query

    def _apply_pagination(self, base_query: Query) -> Query:
        return base_query.offset(
            (self.query_params.page - 1) * self.query_params.page_size
        ).limit(self.query_params.page_size)
