from uuid import UUID

from sqlalchemy.orm import Session, Query

from app.operations.tenant.get_active_subscription_plan import GetTenantSubscriptionPlanOperation
from app.models.permission import Permission
from app.models.permission_group_permission import PermissionGroupPermission
from app.models.user import User
from app.schemas.tenant import ListTenantPermissionsQueryParams


class GetTenantPermissionsOperation:
    def __init__(
        self,
        db: Session,
        current_user: User,
        tenant_id: UUID,
        query_params: ListTenantPermissionsQueryParams,
    ):
        self.db = db
        self.current_user = current_user
        self.tenant_id = tenant_id
        self.query_params = query_params

    def execute(self):
        self._get_current_active_subscription_plan()
        
        base_query = self._build_base_query()
        base_query = self._apply_filters(base_query)
        base_query = self._apply_ordering(base_query)
        
        total = base_query.count()
        permissions = self._apply_pagination(base_query).all()

        return total, permissions
        
    def _get_current_active_subscription_plan(self):
        operation = GetTenantSubscriptionPlanOperation(self.db, self.current_user, self.tenant_id)
        self.current_active_subscription_plan = operation.execute()

    def _build_base_query(self):
        return (
            self.db.query(Permission)
            .join(
                PermissionGroupPermission,
                Permission.id == PermissionGroupPermission.permission_id,
            )
            .filter(
                Permission.is_enabled.is_(True),
                PermissionGroupPermission.permission_group_id == self.current_active_subscription_plan.permission_group_id,
            )
        )
        
    def _apply_filters(self, base_query: Query):
        if self.query_params.search:
            base_query = base_query.filter(Permission.name.ilike(f"%{self.query_params.search}%"))

        return base_query
    
    def _apply_ordering(self, base_query: Query):
        if self.query_params.order_by:
            if self.query_params.order_direction == "desc":
                base_query = base_query.order_by(getattr(Permission, self.query_params.order_by).desc())
            else:
                base_query = base_query.order_by(getattr(Permission, self.query_params.order_by).asc())
        else:
            base_query = base_query.order_by(Permission.code.asc())

        return base_query
    
    def _apply_pagination(self, base_query: Query):
        return base_query.offset(
            (self.query_params.page - 1) * self.query_params.page_size
        ).limit(self.query_params.page_size)
