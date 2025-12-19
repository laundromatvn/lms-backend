from typing import List
from sqlalchemy.orm import Session, Query

from app.models.user import User
from app.models.store import Store
from app.models.store_member import StoreMember
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.schemas.store import ListStoreQueryParams


class ListStoresOperation:

    def __init__(
        self, 
        db: Session, 
        current_user: User, 
        query_params: ListStoreQueryParams,
    ):
        self.db = db
        self.current_user = current_user
        self.query_params = query_params

    def execute(self) -> tuple[int, List[Store]]:
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
        base_query = self.db.query(
            *Store.__table__.columns,
            Tenant.name.label("tenant_name"),
        ).join(Tenant, Store.tenant_id == Tenant.id)

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
        if self.query_params.tenant_id:
            base_query = base_query.filter(
                Store.tenant_id == self.query_params.tenant_id
            )

        if self.query_params.status:
            base_query = base_query.filter(Store.status == self.query_params.status)
            
        if self.query_params.search:
            base_query = base_query.filter(
                Store.name.ilike(f"%{self.query_params.search}%")
            )

        return base_query
    
    def _apply_ordering(self, base_query: Query) -> Query:
        if not self.query_params.order_by: return base_query
        
        if self.query_params.order_by == "tenant_name":
            if self.query_params.order_direction == "desc":
                base_query = base_query.order_by(Tenant.name.desc())
            else:
                base_query = base_query.order_by(Tenant.name.asc())
        elif self.query_params.order_by:
            if self.query_params.order_direction == "desc":
                base_query = base_query.order_by(getattr(Store, self.query_params.order_by).desc())
            else:
                base_query = base_query.order_by(getattr(Store, self.query_params.order_by).asc())
        else:
            base_query = base_query.order_by(Store.created_at.desc())

        return base_query
