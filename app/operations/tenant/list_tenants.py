from sqlalchemy.orm import Session, Query

from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.tenant import ListTenantQueryParams


class ListTenantsOperation:
    def __init__(
        self, db: Session, current_user: User, query_params: ListTenantQueryParams
    ):
        self.db = db
        self.current_user = current_user
        self.query_params = query_params

    def execute(self) -> tuple[int, list[Tenant]]:
        base_query = self._build_base_query()

        base_query = self._apply_filters(base_query)
        base_query = self._apply_ordering(base_query)
        base_query = self._apply_pagination(base_query)
        
        total = base_query.count()
        tenants = base_query.all()

        return total, tenants
    
    def _build_base_query(self) -> Query:
        base_query = (
            self.db.query(Tenant)
            .filter(Tenant.deleted_at.is_(None))
        )

        return base_query

    def _apply_filters(self, base_query: Query) -> Query:
        if self.query_params.status:
            base_query = base_query.filter(Tenant.status == self.query_params.status)

        if self.query_params.search:
            base_query = base_query.filter(
                Tenant.name.ilike(f"%{self.query_params.search}%")
            )

        return base_query

    def _apply_ordering(self, base_query: Query) -> Query:
        if self.query_params.order_by:
            if self.query_params.order_direction == "desc":
                base_query = base_query.order_by(Tenant.name.desc())
            else:
                base_query = base_query.order_by(Tenant.name.asc())
        else:
            base_query = base_query.order_by(Tenant.created_at.desc())

        return base_query

    def _apply_pagination(self, base_query: Query) -> Query:
        return base_query.offset(
            (self.query_params.page - 1) * self.query_params.page_size
        ).limit(self.query_params.page_size)
