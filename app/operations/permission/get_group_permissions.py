from uuid import UUID

from sqlalchemy.orm import Session, Query

from app.models.permission_group_permission import PermissionGroupPermission
from app.models.tenant_member import TenantMember
from app.models.permission import Permission
from app.models.user import User
from app.schemas.permission import ListGroupPermissionsQueryParams


class GetGroupPermissionsOperation:

    def __init__(
        self,
        db: Session,
        current_user: User,
        permission_group_id: UUID,
        query_params: ListGroupPermissionsQueryParams,
    ):
        self.db = db
        self.current_user = current_user
        self.permission_group_id = permission_group_id
        self.query_params = query_params

    def execute(self) -> tuple[int, list[Permission]]:
        base_query = self._build_base_query()
        base_query = self._apply_filters(base_query)
        base_query = self._apply_ordering(base_query)
        
        total = base_query.count()
        permissions = self._apply_pagination(base_query).all()

        return total, permissions
    
    def validate(self) -> None:
        if self.current_user.is_admin:
            return

        tenant_members = (
            self.db.query(TenantMember)
            .filter(
                TenantMember.user_id == self.current_user.id,
                TenantMember.tenant_id == self.permission_group_id,
                TenantMember.is_enabled == True,
            )
            .first()
        )
        if not tenant_members:
            raise PermissionError("You are not a member of this tenant")

    def _build_base_query(self) -> Query:
        return (
            self.db.query(Permission)
            .join(PermissionGroupPermission, Permission.id == PermissionGroupPermission.permission_id)
            .filter(PermissionGroupPermission.permission_group_id == self.permission_group_id)
        )

    def _apply_filters(self, base_query: Query) -> Query:
        if self.query_params.search:
            return base_query.filter(Permission.name.ilike(f"%{self.query_params.search}%"))

        return base_query
    
    def _apply_ordering(self, base_query: Query) -> Query:
        if self.query_params.order_by:
            return base_query.order_by(getattr(Permission, self.query_params.order_by).asc())

        return base_query
    
    def _apply_pagination(self, base_query: Query) -> Query:
        return base_query.offset(
            (self.query_params.page - 1) * self.query_params.page_size
        ).limit(self.query_params.page_size)
