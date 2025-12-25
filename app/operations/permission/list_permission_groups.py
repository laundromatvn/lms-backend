from sqlalchemy.orm import Session, Query

from app.models.permission_group import PermissionGroup
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.permission import ListPermissionGroupsQueryParams


class ListPermissionGroupsOperation:

    def __init__(
        self,
        db: Session,
        current_user: User,
        query_params: ListPermissionGroupsQueryParams,
    ) -> None:
        self.db = db
        self.current_user = current_user
        self.query_params = query_params

    def execute(self) -> tuple[int, list[PermissionGroup]]:            
        self._validate_user()

        base_query = self._build_base_query()

        base_query = self._apply_scope(base_query)
        base_query = self._apply_filters(base_query)
        base_query = self._apply_ordering(base_query)
        base_query = self._apply_pagination(base_query)

        total = base_query.count()
        permission_groups = base_query.all()

        return total, permission_groups

    def _validate_user(self) -> None:
        if self.current_user.is_admin:
            return

        if not self.current_user.is_tenant_admin:
            raise PermissionError("You are not allowed to list permission groups")

    def _build_base_query(self) -> Query:
        base_query = (
            self.db.query(
                *PermissionGroup.__table__.columns,
                Tenant.name.label("tenant_name"),
            )
            .join(Tenant, PermissionGroup.tenant_id == Tenant.id, isouter=True)
        )

        return base_query

    def _apply_scope(self, base_query: Query) -> Query:
        if self.current_user.is_admin:
            return base_query

        if self.current_user.is_tenant_admin:
            return base_query.filter(
                PermissionGroup.tenant_id == self.current_user.tenant_id,
                PermissionGroup.tenant_id == None,
            )

    def _apply_filters(self, base_query: Query) -> Query:
        if self.query_params.tenant_id:
            return base_query.filter(PermissionGroup.tenant_id == self.query_params.tenant_id)
        
        if self.query_params.search:
            return base_query.filter(PermissionGroup.name.ilike(f"%{self.query_params.search}%"))

        return base_query
    
    def _apply_ordering(self, base_query: Query) -> Query:
        if self.query_params.order_by:
            if self.query_params.order_direction == "desc":
                base_query = base_query.order_by(PermissionGroup.name.desc())
            else:
                base_query = base_query.order_by(PermissionGroup.name.asc())
        else:
            base_query = base_query.order_by(PermissionGroup.created_at.desc())

        return base_query
    
    def _apply_pagination(self, base_query: Query) -> Query:
        return base_query.offset(
            (self.query_params.page - 1) * self.query_params.page_size
        ).limit(self.query_params.page_size)
